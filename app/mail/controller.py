import imaplib
import email
import email.utils
import email.generator
import mailparser
import json
import time 
import pytz
import os
import base64
import quopri
import re
import smtplib
import ssl

from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from app.general_utility import toList, convertStrToDate
import imaplib
from app import SCHEDULER, CURRENT_NOW
from itertools import chain
from email.header import decode_header, make_header
from io import StringIO
from os.path import basename
from app.s3.controller import uploadFileToS3, uploadContentImageToS3
from app.mail.model import  (
    insertEmailAttachments,
    selectMailCritical,
    insertEmail,
    updateTypeEmailByMessageId,
    selectEmailByMessageID,
    selectFilterActive,
    selectFilterConditionByFIlterId,
    selectFilterActionByFIlterId,
    updateStatusEmailByMessageId,
    insertEmailTag,
    selectTagByID,
    updateEmailCriticalType,
)
from dotenv import load_dotenv

load_dotenv()
IMAP_HOST = os.getenv('IMAP_HOST')
IMAP_PORT = os.getenv('IMAP_PORT')
MAIL_USERNAME = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
SMTP_HOST = os.getenv('SMTP_HOST')
SMTP_PORT= os.getenv('SMTP_PORT')

class Attachment:
    def __init__(self, part, filename=None, type=None, payload=None, charset=None, content_id=None, description=None, disposition=None, sanitized_filename=None, is_body=None):
        self.part=part          # original python part
        self.filename=filename  # filename in unicode (if any) 
        self.type=type          # the mime-type
        self.payload=payload    # the MIME decoded content 
        self.charset=charset    # the charset (if any) 
        self.description=description    # if any 
        self.disposition=disposition    # 'inline', 'attachment' or None
        self.sanitized_filename=sanitized_filename # cleanup your filename here (TODO)  
        self.is_body=is_body        # usually in (None, 'text/plain' or 'text/html')
        self.content_id=content_id  # if any
        if self.content_id:
            # strip '<>' to ease searche and replace in "root" content (TODO) 
            if self.content_id.startswith('<') and self.content_id.endswith('>'):
                self.content_id=self.content_id[1:-1]

def getmailheader(header_text, default="utf-8"):
    """Decode header_text if needed"""
    try:
        headers = decode_header(header_text)
    except email.errors.HeaderParseError:
        # This already append in email.base64mime.decode()
        # instead return a sanitized ascii string
        # this faile '=?UTF-8?B?15HXmdeh15jXqNeVINeY15DXpteUINeTJ9eV16jXlSDXkdeg15XXldeUINem15PXpywg15TXptei16bXldei15nXnSDXqdecINek15zXmdeZ?==?UTF-8?B?157XldeR15nXnCwg157Xldek16Ig157Xl9eV15wg15HXodeV15bXnyDXk9ec15DXnCDXldeh15gg157Xl9eR16rXldeqINep15wg15HXmdeQ?==?UTF-8?B?15zXmNeZ?='
        return header_text.encode('utf-8', 'replace').decode('utf-8')
    else:
        for i, (text, charset) in enumerate(headers):
            try:
                headers[i] = str(text, charset)
            except:
                # if the charset is unknown, force default 
                headers[i] = text
        return headers[0]

def encoded_words_to_text(encoded_words):
    encoded_word_regex = r'=\?{1}(.+)\?{1}([B|Q])\?{1}(.+)\?{1}='
    charset, encoding, encoded_text = re.match(encoded_word_regex, encoded_words).groups()
    if encoding is 'B':
        byte_string = base64.b64decode(encoded_text)
    elif encoding is 'Q':
        byte_string = quopri.decodestring(encoded_text)
    if charset == 'windows-874':
        charset = 'cp874'
    return byte_string.decode(charset)

def get_filename(part):
    """Many mail user agents send attachments with the filename in 
    the 'name' parameter of the 'content-type' header instead 
    of in the 'filename' parameter of the 'content-disposition' header.
    """
    filename=part.get_param('filename', None, 'content-disposition')
    if not filename:
        filename=part.get_param('name', None) # default is 'content-type'
        
    if filename:
        # RFC 2231 must be used to encode parameters inside MIME header
        filename=email.utils.collapse_rfc2231_value(filename).strip()

    if filename and isinstance(filename, str):
        # But a lot of MUA erroneously use RFC 2047 instead of RFC 2231
        # in fact anybody miss use RFC2047 here !!!
        filename=getmailheader(filename)
        
    return filename

def _search_message_bodies(bodies, part):
    """recursive search of the multiple version of the 'message' inside 
    the the message structure of the email, used by search_message_bodies()"""
    
    type=part.get_content_type()
    if type.startswith('multipart/'):
        # explore only True 'multipart/*' 
        # because 'messages/rfc822' are also python 'multipart' 
        if type=='multipart/related':
            # the first part or the one pointed by start 
            start=part.get_param('start', None)
            related_type=part.get_param('type', None)
            for i, subpart in enumerate(part.get_payload()):
                if (not start and i==0) or (start and start==subpart.get('Content-Id')):
                    _search_message_bodies(bodies, subpart)
                    return
        elif type=='multipart/alternative':
            # all parts are candidates and latest is best
            for subpart in part.get_payload():
                _search_message_bodies(bodies, subpart)
        elif type in ('multipart/report',  'multipart/signed'):
            # only the first part is candidate
            try:
                subpart=part.get_payload()[0]
            except IndexError:
                return
            else:
                _search_message_bodies(bodies, subpart)
                return

        elif type=='multipart/signed':
            # cannot handle this
            return
            
        else: 
            # unknown types must be handled as 'multipart/mixed'
            # This is the peace of code could probably be improved, I use a heuristic : 
            # - if not already found, use first valid non 'attachment' parts found
            for subpart in part.get_payload():
                tmp_bodies=dict()
                _search_message_bodies(tmp_bodies, subpart)
                for k, v in tmp_bodies.items():
                    if not subpart.get_param('attachment', None, 'content-disposition')=='':
                        # if not an attachment, initiate value if not already found
                        bodies.setdefault(k, v)
            return
    else:
        bodies[part.get_content_type().lower()]=part
        return
    
    return

def search_message_bodies(mail):
    """search message content into a mail"""
    bodies=dict()
    _search_message_bodies(bodies, mail)
    return bodies

def get_mail_contents(msg):
    """split an email in a list of attachments"""

    attachments=[]

    # retrieve messages of the email
    bodies=search_message_bodies(msg)
    # reverse bodies dict
    parts=dict((v,k) for k, v in bodies.items())

    # organize the stack to handle deep first search
    stack=[ msg, ]
    while stack:
        part=stack.pop(0)
        type=part.get_content_type()
        if type.startswith('message/'): 
            # ('message/delivery-status', 'message/rfc822', 'message/disposition-notification'):
            # I don't want to explore the tree deeper her and just save source using msg.as_string()
            # but I don't use msg.as_string() because I want to use mangle_from_=False 
            fp = StringIO()
            g = email.generator.Generator(fp, mangle_from_=False)
            g.flatten(part, unixfrom=False)
            payload=fp.getvalue()
            filename='mail.eml'
            attachments.append(Attachment(part, filename=filename, type=type, payload=payload, charset=part.get_param('charset'), description=part.get('Content-Description')))
        elif part.is_multipart():
            # insert new parts at the beginning of the stack (deep first search)
            stack[:0]=part.get_payload()
        else:
            payload=part.get_payload(decode=True)
            charset=part.get_param('charset')
            filename=get_filename(part)
                
            disposition=None
            if part.get_param('inline', None, 'content-disposition')=='':
                disposition='inline'
            elif part.get_param('attachment', None, 'content-disposition')=='':
                disposition='attachment'
        
            attachments.append(Attachment(part, filename=filename, type=type, payload=payload, charset=charset, content_id=part.get('Content-Id'), description=part.get('Content-Description'), disposition=disposition, is_body=parts.get(part)))

    return attachments

def decode_text(payload, charset, default_charset):
    if charset:
        if charset == 'windows-874' or charset == 'tis-620':
            try:
                return payload.decode('cp874'), charset
            except:
                pass
        try:
            return payload.decode(charset), charset
        except:
            pass

    if default_charset and default_charset!='auto':
        try: 
            return payload.decode(default_charset), default_charset
        except:
            pass
        
    for chset in [ 'ascii', 'utf-8', 'utf-16', 'windows-1252', 'cp850' ]:
        try: 
            return payload.decode(chset), chset
        except:
            pass

    return payload, None

def search_string(uid_max, criteria):
    c = list(map(lambda t: (t[0], '"'+str(t[1])+'"'), criteria.items())) + [('UID', '%d:*' % (uid_max+1))]
    return '(%s)' % ' '.join(chain(*c))

def createDirectory(dir_fd):
    try:
        # Create target Directory
        os.mkdir(dir_fd)
    except FileExistsError:
        pass

def connectImap(folder='"INBOX"'):
    print("connectImap folder : ", folder)
    client = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    client.login(MAIL_USERNAME, MAIL_PASSWORD)

    # for i in client.list()[1]:
    #     l = i.decode().split(' "/" ')
    #     print(l[0] + " = " + l[1])
    
    #print(client.list())
    client.select(folder) # Seletc folder in Email
    print("connect imap success")
    return client

def addTagToEmail(message_id, tag_name, folder='"INBOX"'):
    print("add tag")
    # Connect IMAP
    if "<" in message_id:
        tmp_message_id = message_id.split("<")
        message_id = "<"+tmp_message_id[1]
    client = connectImap(folder=folder)

    #the search command
    result, data = client.uid('search', '(HEADER Message-ID "%s")' % message_id, None)
    uid = data[0]
    uid = uid.decode("utf-8")
    if " " in uid:
        tmp_uid = uid.split(" ")
        for uid in tmp_uid:
            uid = bytes(uid, "utf-8")
            client.uid("STORE", uid, '+FLAGS', tag_name)
    elif uid=="":
        pass
    else:
        uid = bytes(uid, "utf-8")
        client.uid("STORE", uid, '+FLAGS', tag_name)

def removeTagToEmail(message_id, tag_name, folder='"INBOX"'):
    # Connect IMAP
    if "<" in message_id:
        tmp_message_id = message_id.split("<")
        message_id = "<"+tmp_message_id[1]
    client = connectImap(folder=folder)

    #the search command
    result, data = client.uid('search', '(HEADER Message-ID "%s")' % message_id, None)
    uid = data[0]
    uid = uid.decode("utf-8")
    if " " in uid:
        tmp_uid = uid.split(" ")
        for uid in tmp_uid:
            uid = bytes(uid, "utf-8")
            client.uid("STORE", uid, '-FLAGS', tag_name)
    elif uid=="":
        pass
    else:
        uid = bytes(uid, "utf-8")
        client.uid("STORE", uid, '-FLAGS', tag_name)

def writeFileFromMail(mail):
    createDirectory("tmp")
    name_files = []
    i = 1

    for part in mail.walk():
        if part.get_content_maintype() == 'multipart':
            # print part.as_string()
            continue

        if part.get('Content-Disposition') is None:
            # print part.as_string()
            continue

        name_file = part.get_filename()
        #check extension file
        content_type = part.get_content_type()
        if name_file is None:
            name_file = "unknown"
        extension_file_check = name_file.split(".")[-1]
        
        if content_type == "image/bmp" and extension_file_check != "bmp":
            name_file = name_file + ".bmp"
        elif content_type == "image/gif" and extension_file_check != "gif":
            name_file = name_file + ".gif"
        elif content_type == "image/vnd.microsoft.icon" and extension_file_check != "ico":
            name_file = name_file + ".ico"
        elif content_type == "image/jpeg" and extension_file_check != "jpg":
            name_file = name_file + ".jpg"
        elif content_type == "image/png" and extension_file_check != "png":
            name_file = name_file + ".png"
        elif content_type == "image/svg+xml" and extension_file_check != "svg":
            name_file = name_file + ".svg"
        elif content_type == "image/tiff" and extension_file_check != "tif":
            name_file = name_file + ".tif"
        elif content_type == "image/webp" and extension_file_check != "webp":
            name_file = name_file + ".webp"
            
        if bool(name_file):
            if name_file is None:
                name_file = ""
            if "\r\n\t" in name_file:
                tmp = name_file.split("\r\n\t")
                count_loop = 0
                name_file = ""
                while count_loop<len(tmp):
                    tmp_name_file = ""
                    try:
                        tmp_name_file = str(tmp[count_loop], 'utf-8')
                    except:
                        tmp_name_file = tmp[count_loop]
                        pass
                    
                    try:
                        tmp_name_file = encoded_words_to_text(encoded_words=tmp_name_file)
                    except Exception:
                        pass

                    try:
                        tmp_name_file = tmp_name_file.decode("utf-8")
                    except Exception:
                        pass

                    name_file = name_file + tmp_name_file
                    count_loop = count_loop+1

            try:
                name_file = encoded_words_to_text(encoded_words=name_file)
            except Exception:
                pass
            name_file = str(i)+"-"+name_file
            content_type = part.get_content_type()
            try:
                size_file = len(part.get_payload(decode=True))/1024
            except Exception:
                size_file = 0
                continue
            if size_file>1024:
                size_file = size_file/1024
                unit_file = "MB"
            else:
                unit_file = "KB"

            fp = open("tmp/"+name_file, 'wb')
            fp.write(part.get_payload(decode=True))
            fp.close()
            name_files.append({"name_file": name_file, "content_type": content_type, "size_file": str(round(size_file, 2))+" "+unit_file})
            i=i+1

    return name_files


def receiveMailAllFolder():
    print("begin")
    print("HOST: ", IMAP_HOST)
    if "gmail" in IMAP_HOST:
        is_eng = checkGmailLanguage()
        if is_eng:
            folder = ['"INBOX"'] # Spam = Junk
        else:
            folder = ['"INBOX"'] # utf-7 encode
    elif "office365" in IMAP_HOST:
        folder = ['"INBOX"'] # Deleted = Trash
    else:
        folder = ['"INBOX"']
    for item in folder:
        print(item)
        netflixForwardEmail(folder=item)

def checkGmailLanguage():
    print("Check Gmail Language")
    client = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    client.login(MAIL_USERNAME, MAIL_PASSWORD)

    folder = []
    for i in client.list()[1]:
        l = i.decode().split(' "/" ')
        folder.append(l[1])
    
    try:
        if '"[Gmail]/Sent Mail"' in folder:
            print("Gmail is English")
            client.logout()
            return True
        else:
            print("Gmail is Thai")
            client.logout()
            return False
    except Exception:
        print(Exception)
        client.logout()
        return False

def netflixForwardEmail(folder):
    folder = '"INBOX"'
    print("connecting imap")
    
    # Connect IMAP
    client = connectImap(folder=folder)
    CURRENT_NOW = datetime.now(pytz.utc)
    #CURRENT_NOW = datetime.now(pytz.utc) - timedelta(days=5)
    CRITERIA = {
        'FROM': '',
        'SINCE': CURRENT_NOW.date().strftime("%d-%b-%Y")
    }

    # Fetch UID Email
    print("fetching uid")
    result, data = client.uid('search', None, '(UNSEEN)', '(SINCE {date})'.format(date=CRITERIA['SINCE']))
    #result, data = client.uid('search', 'UNSEEN', search_string(0, CRITERIA))
    print("fetch uid success")

    if not data or len(data[0].split()) == 0:
        print("no email fetched")
        client.logout()
        return

    print(len(data[0].split()))
    try:
        uids = [int(s) for s in data[0].split()]
    except ValueError:
        # Handle the case where the data contains unexpected values
        print("Error: Unexpected data from the IMAP server")
        client.logout()
        return
    print("uids: ", uids)
    
    # Loop through the list of email UIDs
    for uid in uids:
        print("fetching mail")
        result, data = client.uid('fetch', str(uid), '(RFC822)')  # Fetch by UID per email
        print("fetch mail success")
        
        # Fetch Get Message ID 's email
        result_message_id, data_message_id = client.uid('fetch', str(uid), '(BODY[HEADER.FIELDS (MESSAGE-ID)])')
        print("fetch header success")
        
        msg_str = email.message_from_bytes(data_message_id[0][1])
        
        try:
            mail = mailparser.parse_from_bytes(data[0][1])
        except Exception:
            try:
                response = data[1]
                mail = mailparser.parse_from_bytes(response[1])
            except Exception:
                try:
                    for item in data:
                        try:
                            mail = mailparser.parse_from_bytes(item)
                            break
                        except Exception:
                            continue
                except Exception:
                    print(data)
                    print(Exception)
                    client.uid("STORE", str(uid), '-FLAGS', '(\Seen)')
                    continue

        mail_header = json.loads(mail.headers_json)  # Get the header

        date = mail_header.get("Date") or mail_header.get("date")
        try:
            date = convertStrToDate(date)
        except Exception:
            date = datetime.now(pytz.utc)

        # Check receive time mail before open function must pass
        if date < CURRENT_NOW:
            # client.uid("STORE", str(uid), '-FLAGS', '(\Seen)')
            # continue
            pass
        try:
            message_id = msg_str.get('Message-ID').replace(" ", "").replace('\n','').replace('\r','')
        except Exception:
            print(Exception)
            pass
        
        try:
            original_email = fetchEmailByMessageID(str(message_id))
        except Exception:
            print(Exception)
            pass
        if original_email is None:
            return print("Original email not found")
        
        forward_subject = f"Fw: {original_email['subject']}"
        forward_body = f"Forwarded email: {original_email['body']}"
        print(forward_body)
        
        toAddr = None
        if "ขอโดย TamWT" in forward_body:
            return print("Is Owner Email")
        elif "ขอโดย Pin" in forward_body:
            print("Pin")
            toAddr = "chananchida2912@gmail.com"
        elif "ขอโดย DOG" in forward_body:
            print("DOG")
            toAddr = "nuttanan355@gmail.com"
        elif "ขอโดย Mini" in forward_body:
            print("Mini")
            toAddr = "chananchida2912@gmail.com"
        elif "ขอโดย Peat" in forward_body:
            print("Peat")
            toAddr = "pansan643@gmail.com"
        else:
            return print("No recipient found")
        
        if toAddr is None:
            return print("No recipient found")
        
        sendMail(
            host=SMTP_HOST,
            port=SMTP_PORT,
            username=MAIL_USERNAME,
            password=MAIL_PASSWORD,
            fromAddr=MAIL_USERNAME,
            toAddr=toAddr,
            ccAddr="",
            bccAddr="",
            subject=forward_subject,
            body=forward_body,
            message_id="",
            fwd=True,
        )

    client.logout()

def sendMail(host, port, username, password, fromAddr, toAddr, ccAddr, bccAddr, subject, body, message_id=None, attachments=[], fwd=False):
    if port != "465":
        server = smtplib.SMTP(host, port)
        if port != "25":
            server.connect(host, port)
            server.ehlo()
            server.starttls()
            server.ehlo()
        server.login(username, password)
    else:
        context = ssl.create_default_context()
        server = smtplib.SMTP_SSL(host, port, context=context)
        server.connect(host, port)
        server.login(username, password)
    
    if ccAddr is None:
        ccAddr = ""

    if bccAddr is None:
        bccAddr = ""
    regex = re.compile(r'(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b')
    
    tmp_to = regex.findall(toAddr)
    toAddr = ""
    for item in tmp_to:
        if item in toAddr:
            continue
        toAddr = toAddr+","+item
    toAddr = toAddr.replace(",","",1)

    tmp_cc = regex.findall(ccAddr)
    ccAddr = ""
    for item in tmp_cc:
        if item in ccAddr:
            continue
        ccAddr = ccAddr+","+item
    ccAddr = ccAddr.replace(",","",1)

    tmp_bcc = regex.findall(bccAddr)
    bccAddr = ""
    for item in tmp_bcc:
        if item in bccAddr:
            continue
        bccAddr = bccAddr+","+item
    bccAddr = bccAddr.replace(",","",1)

    msg = MIMEMultipart("alternative")
    msg["From"] = fromAddr
    msg["To"] = toAddr

    tmp = ccAddr.split(",")
    ccAddr = ""

    for item in tmp:
        if item is None or item == "None":
            continue
        if item in ccAddr:
            continue
        ccAddr = ccAddr+","+item
    
    ccAddr = ccAddr.replace(",","",1)
    msg["Cc"] = ccAddr
    msg["Bcc"] = bccAddr
    msg["Date"] = email.utils.formatdate(localtime=True)
    
    if message_id: #check if reply mail
        if fwd:
            msg["Subject"] = "FWD : " +  subject
        else:
            msg["Subject"] = "RE : " +  subject
        msg["Message-ID"] = email.utils.make_msgid()
        msg["In-Reply-To"] = message_id
        msg["References"] = message_id
    else:
        msg["Subject"] = subject

    msg.attach(MIMEText(body, "html", "utf-8"))

    for f in attachments or []: #attachments file upload
        part = MIMEApplication((f.read()), Name=basename(f.filename))
        part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f.filename)
        msg.attach(part)
    text = msg.as_string()
    
    saveMailInSentBox(text) #Save email in Sent Folder
    destination = []
    if "," in msg["To"]:
        toAddr = msg["To"].split(",")
        for item in toAddr:
            destination.append(item)
    else:
        if msg["To"] != "":
            destination.append(msg["To"])
    if "," in msg["Cc"]:
        ccAddr = msg["Cc"].split(",")
        for item in ccAddr:
            destination.append(item)
    else:
        if msg["Cc"] != "":
            destination.append(msg["Cc"])
    if "," in msg["Bcc"]:
        bccAddr = msg["Bcc"].split(",")
        for item in bccAddr:
            destination.append(item)
    else:
        if msg["Bcc"] != "":
            destination.append(msg["Bcc"])
    server.sendmail(msg["From"], destination, text)
    server.quit()
    return "success"

def saveMailInSentBox(text):
    try:
        server = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        server.login(MAIL_USERNAME, MAIL_PASSWORD)
        server.append("Sent", "", imaplib.Time2Internaldate(time.time()), text.encode('utf-8'))
        server.logout()
    except Exception as e:
        print(f"Failed to save email: {e}")
        return None

def fetchEmailByMessageID(message_id):
    try:
        # Connect to the IMAP server
        imap_server = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        imap_server.login(MAIL_USERNAME, MAIL_PASSWORD)

        # Search for the email with the specified message_id
        imap_server.select("inbox")  # You may need to specify the mailbox

        # Search for the email based on message_id
        search_query = f"HEADER Message-ID {message_id}"
        _, data = imap_server.search(None, search_query)

        # Get the email IDs matching the search
        email_ids = data[0].split()

        if not email_ids:
            print("Email not found")
            return None

        # Fetch the email by ID
        _, msg_data = imap_server.fetch(email_ids[0], "(RFC822)")

        # Parse the email content
        raw_email = msg_data[0][1]
        email_message = email.message_from_bytes(raw_email)

        # You can access email attributes like subject, sender, body, etc.
        subject = decode_header(email_message["Subject"])[0][0]
        sender = email_message["From"]
        body = ""

        if email_message.is_multipart():
            for part in email_message.walk():
                #content_type html
                if part.get_content_type() == "text/html":
                    content = part.get_payload(decode=True)
                    content = content.decode("utf-8")
                    body = content
                    break
        else:
            body = email_message.get_payload(decode=True).decode("utf-8")
        
        #decode subject
        try:
            subject = str(subject, 'utf-8')
        except:
            pass
        
        # Close the IMAP connection
        imap_server.logout()

        return {
            "subject": subject,
            "sender": sender,
            "body": body,
            # Add other email attributes as needed
        }

    except Exception as e:
        print(f"Failed to fetch email: {e}")
        return None