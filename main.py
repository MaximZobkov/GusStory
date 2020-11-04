import os
import datetime
from flask import Flask, render_template, redirect, request, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, BooleanField, IntegerField
from wtforms.validators import DataRequired
import feedparser
from data import db_session, items, users, quests, news

app = Flask(__name__)
app.config['SECRET_KEY'] = 'GusStory.ru'
db_session.global_init("db/blogs.sqlite")
login_manager = LoginManager()
login_manager.init_app(app)
count_items = 0
i = 0
name = 0


@login_manager.user_loader
def load_user(user_id):
    sessions = db_session.create_session()
    return sessions.query(users.User).get(user_id)


class LoginForm(FlaskForm):
    login = StringField("Логин", validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class RegisterForm(FlaskForm):
    name = StringField('Имя', validators=[DataRequired()])
    surname = StringField('Фамилия', validators=[DataRequired()])
    login = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')


class ItemsForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired()])
    content = TextAreaField('Описание достопримечательности')
    year = StringField('Год открытия достопримечательности')
    submit = SubmitField('Применить')


class EditForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired()])
    content = TextAreaField('Описание достопримечательности')
    submit = SubmitField('Применить')


class QuestsForm(FlaskForm):
    name = StringField('Название квеста', validators=[DataRequired()])
    points = TextAreaField('Описание квеста')
    kol_vo = IntegerField("Количество вопросов")
    ok = SubmitField("Ок")
    questions = TextAreaField('Вопрос')
    ansvers = TextAreaField('Ответ')
    submit = SubmitField('Применить')


class AnsverForm(FlaskForm):
    ansver = TextAreaField("Ответ")
    submit = SubmitField("Ответить")


class LengthError(Exception):
    error = 'Пароль должен от 8 до 15 символов!'


class LetterError(Exception):
    error = 'В пароле должна быть хотя бы одна буква!'


class DigitError(Exception):
    error = 'В пароле должна быть хотя бы одна цифра!'


@app.route('/profile')
def profile():
    if current_user.is_authenticated:
        return render_template("profile.html")
    return redirect('/')


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')


def reformat(s):
    s = s.split('-')
    print(s)
    k = 0
    string = ''
    month = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября',
             'декабря']
    for x in s[::-1]:
        if k == 0:
            string += x + ' '
        elif k == 1:
            string += month[int(x) - 1] + ' '
        else:
            string += x + ' ' + 'года'
        k += 1
        print(string)
    return string


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        result = check_password(form.password.data)
        if result != 'OK':
            return render_template('register.html',
                                   title='Регистрация',
                                   form=form, email_error="OK", again_password_error="OK",
                                   password_error=result)
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form, email_error="OK", password_error="OK",
                                   again_password_error="Пароли не совпадают")
        sessions = db_session.create_session()
        if sessions.query(users.User).filter(users.User.login == form.login.data).first():
            return render_template('register.html', title='Регистрация', form=form,
                                   password_error="OK", again_password_error="OK",
                                   email_error="Такой пользователь уже есть")
        user = users.User()
        user.login = form.login.data.lower()
        user.name = form.name.data
        user.created_date = reformat(str(datetime.datetime.now())[:-16])
        user.surname = form.surname.data
        user.set_password(form.password.data)
        user.not_completed = ';'.join(map(lambda x: x.name, sessions.query(quests.Quests)))
        sessions.add(user)
        sessions.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form, email_error="OK",
                           password_error="OK", again_password_error="OK")


def check_password(password):
    flags = [0, 0]
    for element in password:
        if element.isdigit():
            flags[0] = 1
        elif element.isalpha():
            flags[1] = 1
    try:
        if flags[1] == 0:
            raise LetterError
        if flags[0] == 0:
            raise DigitError
        if len(password) < 8 or len(password) > 15:
            raise LengthError
        return 'OK'
    except (LengthError, LetterError, DigitError) as ex:
        return ex.error


@app.route('/items', methods=['GET', 'POST'])
@login_required
def add_items():
    global count_items
    if current_user.id not in [1, 2, 3]:
        return redirect('/')
    form = ItemsForm()
    if form.validate_on_submit():
        sessions = db_session.create_session()
        item = items.Items()
        item.title = form.title.data
        item.content = form.content.data
        f = request.files.getlist("file")
        os.mkdir('static/images/item' + str(count_items + 1))
        count_photo = 0
        photo = request.files['file1']
        photo.save('static/img/image' + str(count_items) + '.png')
        item.photo = '/static/img/image' + str(count_items) + '.png'
        for x in f:
            x.save('static/images/item' + str(count_items + 1) + '/image' + str(count_photo) + '.png')
            item.image = 'static/images/item' + str(count_items + 1)
            count_photo += 1
        item.year = form.year.data
        item.count_photo = count_photo
        sessions.add(item)
        sessions.commit()
        count_items += 1
        return redirect('/')
    return render_template('items.html', title='Добавление товара', form=form)


@app.route('/items/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_items(id):
    if current_user.id not in [1, 2, 3]:
        return redirect('/')
    form = EditForm()
    if request.method == 'GET':
        sessions = db_session.create_session()
        item = sessions.query(items.Items).filter(items.Items.id == id).first()
        form.title.data = item.title
        form.content.data = item.content
    if form.validate_on_submit():
        sessions = db_session.create_session()
        item = sessions.query(items.Items).filter(items.Items.id == id).first()
        item.title = form.title.data
        item.content = form.content.data
        sessions.commit()
        return redirect('/')
    return render_template('editor.html', title='Редактирование товара', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        sessions = db_session.create_session()
        user = sessions.query(users.User).filter(users.User.login ==
                                                 form.login.data.lower()).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect('/')
        return render_template('login.html', message='Неправильный логин или пароль', form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/')
def index():
    sessions = db_session.create_session()
    item = sessions.query(items.Items)
    return render_template("index.html", items=item)


@app.route('/add_quests', methods=['GET', 'POST'])
@login_required
def add_quest():
    global i, name
    if current_user.id not in [1, 2, 3]:
        return redirect('/')
    form = QuestsForm()
    if form.ok.data:
        i = form.kol_vo.data
        sessions = db_session.create_session()
        quest = quests.Quests()
        quest.name = form.name.data
        name = form.name.data
        for user in sessions.query(users.User):
            if user.not_completed is None:
                user.not_completed = quest.name
            else:
                user.not_completed += ';' + quest.name
        quest.points = form.points.data
        sessions.add(quest)
        sessions.commit()
        form.name.data = name
        return render_template('add_quests.html', title='Добавление квеста', form=form, flag=1, i=i)
    if form.submit.data:
        sessions = db_session.create_session()
        i -= 1
        print(name)
        quest = sessions.query(quests.Quests).filter(quests.Quests.name == name).first()
        quest.questions += ";;" + form.questions.data
        quest.ansver += ";;" + form.ansvers.data
        sessions.commit()
        form.questions.data = ""
        form.ansvers.data = ""
        if i == 0:
            return redirect('/quests')
        else:
            return render_template('add_quests.html', title='Добавление квеста', form=form, flag=1, i=i)
    return render_template('add_quests.html', title='Добавление квеста', form=form, flag=0)


@app.route('/quests')
def gus_quests():
    sessions = db_session.create_session()
    quest = sessions.query(quests.Quests)
    return render_template("quests.html", quests=quest)


@app.route("/quest/<int:id>", methods=["GET", "POST"])
@login_required
def gus_quest_item(id):
    sessions = db_session.create_session()
    form = AnsverForm()
    quest = sessions.query(quests.Quests).get(id)
    user = sessions.query(users.User).get(current_user.id)
    ansver_list = current_user.quest_ansver.split("$$")
    print(9)
    print(current_user.quest_ansver)
    f = 0
    if request.method == "POST":
        print(1)
        for i in range(len(ansver_list)):
            ans = ansver_list[i].split("%%")
            if ans[0] == quest.name:
                print(3)
                ans[-1] = str(form.ansver.data)
                if i == 0:
                    ansver_list = ["%%".join(ans)] + ansver_list[i + 1:]
                elif i == len(ansver_list) - 1:
                    ansver_list = ansver_list[:i] + ["%%".join(ans)]
                else:
                    ansver_list = ansver_list[:i] + ["%%".join(ans)] + ansver_list[i + 1:]
                user.quest_ansver = "$$".join(ansver_list)
                sessions.commit()
                break
    user = sessions.query(users.User).get(current_user.id)
    print(2)
    vopros = ""
    number = 0
    otvet = ""
    verno = 0
    ansver_list = user.quest_ansver.split("$$")
    for i in range(len(ansver_list)):
        ans = ansver_list[i].split("%%")
        if ans[0] == quest.name:
            f = 1
            number = len(ans) - 1
            vopros = quest.questions.split(";;")[number]
            tru_ans = quest.ansver.split(";;")[number]
            otvet = ans[number]
            print(6, otvet, number, vopros)
            if tru_ans == otvet:
                form.ansver.data = ""
                if number == len(quest.questions.split(";;")) - 1:
                    if quest.name not in user.completed.split(";"):
                        user.completed = ";".join(user.completed.split(";") + [quest.name])
                        not_com = user.not_completed.split(";")
                        num = -1
                        print(not_com)
                        for j in range(len(not_com)):
                            print(not_com[j], quest.name, not_com[j] == quest.name, 9999999)
                            if not_com[j] == quest.name:
                                num = j
                                break
                        print(num, 66666666)
                        if num != -1:
                            if num == 0:
                                user.not_completed = ";".join(not_com[num + 1:])
                            elif num == len(not_com) - 1:
                                user.not_completed = ";".join(not_com[:num])
                            else:
                                user.not_completed = ";".join(not_com[:num] + not_com[num + 1:])
                        sessions.commit()
                    return render_template("quest_item.html", quest=quest, message="Vin")
                verno = 1
                number += 1
                vopros = quest.questions.split(";;")[number]
                otvet = ""
                if i != 0:
                    ansver_list = ["%%".join(ans) + "%%"] + ansver_list[i + 1:]
                elif i == len(ansver_list) - 1:
                    ansver_list = ansver_list[:i] + ["%%".join(ans) + "%%"]
                else:
                    ansver_list = ansver_list[:i] + ["%%".join(ans) + "%%"] + ansver_list[i + 1:]
                user.quest_ansver = "$$".join(ansver_list)
                sessions.commit()
            break
    if f == 0:
        print(4)
        if user.quest_ansver == "":
            user.quest_ansver = quest.name + "%%"
        else:
            user.quest_ansver = user.quest_ansver + "$$" + quest.name + "%%"
        sessions.commit()
        number = 1
        vopros = quest.questions.split(";;")[number]
        otvet = ""
        verno = 1
    return render_template("quest_item.html", quest=quest, form=form, num=number, vopr=vopros, otv=otvet, ver=verno)


@app.route("/erase_quest/<int:id>")
@login_required
def erase_quest(id):
    if not current_user.id in [1, 2, 3]:
        return redirect("/")
    sessions = db_session.create_session()
    quest = sessions.query(quests.Quests).get(id)
    usery = sessions.query(users.User)
    for user in usery:
        try:
            st = user.completed
            st2 = user.not_completed
            number = str(st).find(str(quest.name))
            number2 = str(st2).find(str(quest.name))
            if number != -1:
                user.completed = st[:number - 1] + st[number + len(str(quest.name)):]
            if number2 != -1:
                user.not_completed = st2[:number2 - 1] + st2[number2 + len(str(quest.name)):]
        except:
            pass
        sessions.commit()
    sessions.delete(quest)
    sessions.commit()
    return redirect("/quests")


@app.route('/about_item/<int:id>', methods=['GET', 'POST'])
def about_item(id):
    sessions = db_session.create_session()
    item = sessions.query(items.Items).get(id)
    return render_template("single_item.html", item=item)


"""@app.route("/news")
def view_news():
    session = db_session.create_session()
    news_list = session.query(news.News)
    return render_template("news_item.html", new_list=news_list)
"""

@app.route("/maps")
def maps():
    return render_template("maps.html")


def news_theft():
    try:
        NewsFeedTourism33 = feedparser.parse("https://www.tourism33.ru/events/rss/")
        news_theft_add_to_db(NewsFeedTourism33["entries"], "tourism33")
        clean_news("tourism33")
    except:
        pass
    try:
        NewsFeedCulture = feedparser.parse("https://news.yandex.ru/culture.rss")
        news_theft_add_to_db(NewsFeedCulture["entries"], "Culture")
        clean_news("Culture")
    except:
        pass
    try:
        NewsFeedTravel = feedparser.parse("https://news.yandex.ru/travels.rss")
        news_theft_add_to_db(NewsFeedTravel["entries"], "Travel")
        clean_news("Travel")
    except:
        pass
    try:
        NewsFeedVladimir = feedparser.parse("https://news.yandex.ru/Vladimir/index.rss")
        news_theft_add_to_db(NewsFeedVladimir["entries"], "Vladimir")
        clean_news("Vladimir")
    except:
        pass


def news_theft_add_to_db(nowosty, theme):
    session = db_session.create_session()
    for new in nowosty[:10]:
        if session.query(news.News).filter(news.News.title == new["title"]).count() == 0:
            print(-1)
            new_to_db = news.News()
            new_to_db.title = new["title"]
            try:
                new_to_db.content = new["summary"]
            except:
                new_to_db.content = new["yandex_full-text"]
            new_to_db.theme = theme
            new_to_db.date = datetime.datetime.now()
            session.add(new_to_db)
            session.commit()
    session.commit()
    session.close()


def clean_news(theme):
    sessions = db_session.create_session()
    news_item = sessions.query(news.News).filter(news.News.theme == theme)
    len_new = news_item.count()
    count = 0
    for new in news_item[::-1]:
        if len_new - count > 10:
            sessions.delete(new)
            count += 1
    sessions.commit()
    sessions.close()


@app.route('/news_item/<int:id>')
def about_news(id):
    sessions = db_session.create_session()
    new = sessions.query(news.News).get(id)
    return render_template("item_news.html", new=new)


def main():
    global count_items
    sessions = db_session.create_session()
    count_items += len(list(sessions.query(items.Items)))
    sessions.close()
    app.run()


if __name__ == '__main__':
    #news_theft()
    main()
