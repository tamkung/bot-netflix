from config import CONFIG as ENV_CONFIG
from sqlalchemy import (create_engine,text)

def insertEmailAttachments(message_id, file_name, url, file_size):
    db = create_engine(ENV_CONFIG.DATABASE_URL)
    sql_text = text("""
        INSERT INTO public.email_attachments
        (message_id, file_name, url, file_size)
        Values(:message_id, :file_name, :url, :file_size)
    """)
    
    result = db.execute(
        sql_text,
        message_id=message_id,
        file_name=file_name,
        url=url,
        file_size=file_size
    )
    db.dispose()
    return result

def insertEmail(message_id, header, subject, body, fromAddr, to, cc ,received_at, created_by, in_reply_to, ticket_id, critical_type, status, plain_text, email_type):
    db = create_engine(ENV_CONFIG.DATABASE_URL)
    sql_text = text("""
        INSERT INTO public.emails
        (message_id, "header", subject, body, "from", "to", cc, "received_at", created_at, created_by, updated_at, in_reply_to, ticket_id, critical_type, status, plain_text, type)
        VALUES(:message_id, :header, :subject, :body, :fromAddr, :to, :cc, :received_at, now(), :created_by, now(), :in_reply_to, :ticket_id, :critical_type, :status, :plain_text, :email_type);
    """)
    
    result = db.execute(
        sql_text,
        message_id=message_id,
        header=header,
        subject=subject,
        body=body,
        fromAddr=fromAddr,
        to=to,
        cc=cc,
        received_at=received_at,
        created_by=created_by,
        in_reply_to=in_reply_to,
        ticket_id=ticket_id,
        critical_type=critical_type,
        status=status,
        plain_text=plain_text,
        email_type=email_type
    )
    db.dispose()
    return result

def selectMailCritical(email):
    db = create_engine(ENV_CONFIG.DATABASE_URL_READ)
    sql_text = text("""
        SELECT *
        FROM public.email_noc_critical
        WHERE email = :email 
        AND active_status = true
    """)
    result = db.execute(sql_text, email=email).fetchall()
    db.dispose()
    return result

def updateTypeEmailByMessageId(message_id, type, updated_by):
    db = create_engine(ENV_CONFIG.DATABASE_URL)
    sql_text = text("""
        UPDATE emails
        SET type=(:type), updated_by=(:updated_by)
        WHERE message_id=(:message_id)
    """)
    email = db.execute(sql_text, type=type, updated_by=updated_by, message_id=message_id)
    db.dispose()
    return email

def selectEmailByMessageID(message_id):
    db = create_engine(ENV_CONFIG.DATABASE_URL_READ)
    sql_text = text("""
        SELECT *
        FROM public.emails
        WHERE message_id = :message_id;
    """)
    email = db.execute(sql_text, message_id=message_id)
    result = email.fetchone()
    db.dispose()
    return result

def selectFilterActive():
    db = create_engine(ENV_CONFIG.DATABASE_URL_READ)
    sql_text = text("""
        SELECT * 
        FROM email_filter
        WHERE active_status = true
        ORDER BY priority ASC;
    """)
    filterActive = db.execute(sql_text)
    result = filterActive.fetchall()
    db.dispose()
    return result

def selectFilterConditionByFIlterId(filter_id):
    db = create_engine(ENV_CONFIG.DATABASE_URL_READ)
    sql_text = text("""
        SELECT *
        FROM email_filter_condition
        WHERE filter_id = :filter_id;
    """)
    conditions = db.execute(sql_text, filter_id=filter_id)
    result = conditions.fetchall()
    db.dispose()
    return result

def selectFilterActionByFIlterId(filter_id):
    db = create_engine(ENV_CONFIG.DATABASE_URL_READ)
    sql_text = text("""
        SELECT *
        FROM email_filter_action
        WHERE filter_id = :filter_id;
    """)
    actions = db.execute(sql_text, filter_id=filter_id)
    result = actions.fetchall()
    db.dispose()
    return result

def updateStatusEmailByMessageId(message_id, status, updated_by):
    db = create_engine(ENV_CONFIG.DATABASE_URL)
    sql_text = text("""
        UPDATE public.emails
        SET status=(:status), updated_by=(:updated_by)
        WHERE message_id=(:message_id)
    """)
    email = db.execute(sql_text, status=status, updated_by=updated_by, message_id=message_id)
    db.dispose()
    return email

def insertEmailTag(email_id, tag_id, status):
    db = create_engine(ENV_CONFIG.DATABASE_URL)
    sql_text = text("""
        INSERT INTO public.email_tag
        (email_id, tag_id, status)
        VALUES(:email_id, :tag_id, :status)
    """)
    email_tag = db.execute(sql_text, email_id=email_id, tag_id=tag_id, status=status)
    db.dispose()
    return email_tag

def selectTagByID(tag_id):
    db = create_engine(ENV_CONFIG.DATABASE_URL_READ)
    sql_text = text("""
        SELECT *
        FROM email_noc_mail_tag 
        WHERE id = :tag_id
    """)
    tag = db.execute(sql_text, tag_id=tag_id)
    result = tag.fetchone()
    db.dispose()
    return result

def updateEmailCriticalType(email_id):
    db = create_engine(ENV_CONFIG.DATABASE_URL)
    sql_text = text("""
        UPDATE emails
        SET critical_type=true
        WHERE id=(:email_id)
    """)
    email = db.execute(sql_text, email_id=email_id)
    db.dispose()
    return email