from sqlalchemy import select, insert, update, delete

from db.models import Session, User, Question


def add_user_to_db(user_id, username, first_name, last_name, time_start):
    with Session() as session:
        try:
            query = select(User).where(User.user_id == user_id)
            results = session.execute(query)
            if not results.all():
                stmt = insert(User).values(
                    user_id=user_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    time_start=time_start
                )
                session.execute(stmt)
                session.commit()
        except Exception as e:
            print(e)


def add_question_to_db(user_id, full_name, question, contact, time_contact):
    with Session() as session:
        try:
            stmt = insert(Question).values(
                user_id=user_id,
                full_name=full_name,
                question=question,
                contact=contact,
                time_contact=time_contact
            )
            session.execute(stmt)
            session.commit()
        except Exception as e:
            print(e)


def get_all_questions():
    with Session() as session:
        try:
            query = select(Question)
            questions = session.execute(query)
            query = select(User)
            users = session.execute(query)
            dct_user = {}
            for user in users.scalars():
                start = ''
                if user.time_start:
                    start = user.time_start.strftime('%Y-%m-%d   %H:%M:%S')
                dct_user[user.user_id] = [user.username, user.first_name, user.last_name, start, user.is_block]
            result = [['№', 'id', 'username', 'first_name', 'last_name', 'Время входа в бота',
                       'Как обращаться', 'Вопрос', 'Контакт', 'Время оформления контакта', 'Блокировка бота']]
            cnt = 1
            for question in questions.scalars():
                time_contact = ''
                if question.time_contact:
                    time_contact = question.time_contact.strftime('%Y-%m-%d   %H:%M:%S')
                user_id = question.user_id
                result.append([cnt, user_id, dct_user[user_id][0], dct_user[user_id][1], dct_user[user_id][2],
                               dct_user[user_id][3], question.full_name, question.question, question.contact,
                               time_contact, dct_user[user_id][4]])
                cnt += 1
            return result
        except Exception as e:
            print(e)


def get_all_users():
    with Session() as session:
        try:
            query = select(User)
            users = session.execute(query)
            result = [['№', 'id', 'username', 'first_name', 'last_name', 'Время входа в бота', 'Блокировка бота']]
            cnt = 1
            for user in users.scalars():
                start = ''
                if user.time_start:
                    start = user.time_start.strftime('%Y-%m-%d   %H:%M:%S')
                result.append([cnt, user.user_id, user.username, user.first_name, user.last_name, start, user.is_block])
                cnt += 1
            return result
        except Exception as e:
            print(e)


def delete_all_questions():
    with Session() as session:
        try:
            stmt = delete(Question)
            session.execute(stmt)
            session.commit()
        except Exception as e:
            print(e)

def update_user_blocked(user_id):
    with Session() as session:
        try:
            stmt = update(User).where(User.user_id == user_id).values(is_block=True)
            session.execute(stmt)
            session.commit()
        except Exception as e:
            print(e)


def update_user_unblocked(user_id):
    with Session() as session:
        try:
            stmt = update(User).where(User.user_id == user_id).values(is_block=False)
            session.execute(stmt)
            session.commit()
        except Exception as e:
            print(e)


def get_all_users_unblock():
    with Session() as session:
        query = select(User).where(User.is_block == False)
        users = session.execute(query)
        result = []
        for user in users.scalars():
            result.append(user.id)
    return result
