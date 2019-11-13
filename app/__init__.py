from flask import Flask, render_template, url_for, request, g, redirect, flash, make_response
# from flask_wtf import Form
import datetime
import mysql.connector
import datetime as dt
# import os
import configparser

app = Flask(__name__)
app.config.from_object('config.DevelopConfig')


def set_db_param():
    config = configparser.ConfigParser()
    config.read('config.ini')

    g.host = config['db_param']['host']
    g.user = config['db_param']['user']
    g.password = config['db_param']['password']
    g.app_database = config['db_param']['app_db']
    g.weather_database = config['db_param']['weather_db']


@app.before_request
def before_request():
    set_db_param()
    g.user_cnx = connect_user_db()
    g.weather_cnx = connect_weather_db()
    g.program_ver = '1.41'
    g.ver_date = '2018-07-11'


@app.teardown_appcontext
def close_db(error=None):
    g.user_cnx.close()
    g.weather_cnx.close()


def connect_user_db():
    return mysql.connector.connect(user=g.user, password=g.password,
                                   host=g.host, database=g.app_database)


def connect_weather_db():
    return mysql.connector.connect(user=g.user, password=g.password,
                                   host=g.host, database=g.weather_database)


@app.route("/")
def home():
    now = datetime.datetime.now()
    timestring = now.strftime("%m/%d/%Y %I:%M %p")
    templatedata = {
        'title': 'Job Tracking',
        'time': timestring,
        'ver': g.program_ver,
        'ver_date': g.ver_date
    }

    return render_template('main.html', **templatedata)


@app.route("/login/", methods=['POST'])
def user_login():
    pass


@app.route("/edit-ticket/<action>/<job_number>/", methods=['GET', 'POST'])
def new_ticket_from_database(job_number, action):
    cursor = g.user_cnx.cursor(buffered=True, dictionary=True)
    if request.method == 'GET':
        cursor.execute("SELECT * FROM edit_ticket WHERE job_number = %s;", (job_number,))
        content = cursor.fetchall()[0]

        cursor.execute('SELECT * FROM top_50_co;')

        comment_crlf = content['comment'].decode('UTF-8')
        bindery_crlf = content['bindery'].decode('UTF-8')
        shipping_crlf = content['shipping'].decode('UTF-8')

        return render_template("database-new-ticket.html", title="Job Ticket {}".format(job_number),
                               top_50_co=cursor.fetchall(), print_comment=comment_crlf,
                               print_bindery=bindery_crlf, print_shipping=shipping_crlf, action=action, **content)
    else:
        req_fields = {'customer': None, 'jobname': None}
        usr = request.form
        req_fields['customer'] = usr.get('customer', '')
        req_fields['jobname'] = usr.get('jobname', '')
        cursor.execute('SELECT * FROM top_50_co;')

        if ((req_fields['customer'] == '') or (req_fields['jobname'] == '') or
                (req_fields['customer'] == 'REQUIRED FIELD') or (req_fields['jobname'] == 'REQUIRED FIELD')):
            # Required fields not filled, try again
            # use edit-ticket.html because it remembers entered fields
            return render_template("edit-ticket.html", top_50_co=cursor.fetchall(),
                                   required=req_fields, fields=usr, action=action, job_number=job_number)

        if action == 'repeat':
            try:
                cursor.execute("SELECT * FROM next_jobnumber;")
                new_num = cursor.fetchone()['next_num']
                sql = "insert into job_number values (%s, timestamp(now()));"
                cursor.execute(sql, (new_num,))

                if usr.get('dueDate') == '':
                    due_date = None
                else:
                    due_date = usr.get('dueDate')

                cmd_ticket_detail = ("insert into ticket_detail values (%s, %s, %s, %s, %s, %s, "
                                     "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
                                     "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
                                     "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
                                     "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);")

                cmd_job_detail = ("insert into job_detail values (%s, %s, %s, date(now()), %s, "
                                  "time(now()), %s, %s, timestamp(now()), %s);")

                cursor.execute(cmd_job_detail, (new_num, usr.get('customer', '')[0:65], usr.get('jobname', '')[0:65],
                                                None, "1", request.environ['REMOTE_ADDR'], "0"))

                cursor.execute(cmd_ticket_detail, (new_num, usr.get('prevJob'), usr.get('quote'),
                                                   due_date, usr.get('customer', '')[0:65],
                                                   usr.get('jobname', '')[0:65], usr.get('contact')[0:40],
                                                   usr.get('commentInput'), usr.get('phone')[0:18],
                                                   usr.get('cell')[0:18], usr.get('email')[0:65],
                                                   usr.get('chkEmail'), usr.get('chkCD'),
                                                   usr.get('chkFTP'), usr.get('otherSource')[0:45],
                                                   usr.get('fileName', '')[0:80], usr.get('chkMerge'),
                                                   usr.get('chkDeDupe'), usr.get('chkPresort'),
                                                   usr.get('chkNCOA'), usr.get('chkTNT'),
                                                   usr.get('chkFCM'), usr.get('chkSTD'),
                                                   usr.get('chkNP'), usr.get('chkMeter'),
                                                   usr.get('chkBPM'), usr.get('chkStamp'),
                                                   usr.get('chkPeriodical'), usr.get('chkPostcard'),
                                                   usr.get('chkIndicia'), usr.get('indicia'),
                                                   usr.get('chkMatch'), usr.get('chkCRRT'),
                                                   usr.get('chkListCnt'), usr.get('listCnt'),
                                                   usr.get('chkInkjet'), usr.get('chkLaser'),
                                                   usr.get('chkLabels'), usr.get('chkOutputOther'),
                                                   usr.get('outputOther', '')[0:30], usr.get('jobQty', '')[0:25],
                                                   usr.get('chkFold'), usr.get('chkTab'),
                                                   usr.get('tab', '')[0:1], usr.get('chkInsert'),
                                                   usr.get('insert'), usr.get('chkJumbo'),
                                                   usr.get('chkPoly'), usr.get('chkDuplexColor'),
                                                   usr.get('chkSimplexColor'), usr.get('chkDuplex'),
                                                   usr.get('chkSimplex'), usr.get('stock', '')[0:60],
                                                   dt.datetime.strftime(dt.datetime.now(), "%y-%m-%d"),
                                                   usr.get('rep'), usr.get('binderyInput'),
                                                   usr.get('shippingInput'),
                                                   usr.get('TICKETREF_PLACEHOLDER'),
                                                   usr.get('customerPO', '')[0:20],
                                                   usr.get('linkedBindery')))
                g.user_cnx.commit()

                cursor.execute("select * from select_ticket where job_number = %s;", (new_num,))

                content = cursor.fetchall()[0]
                comment_crlf = content['comment'].decode('UTF-8').replace("\r\n", "<br/>")
                bindery_crlf = content['bindery'].decode('UTF-8').replace("\r\n", "<br/>")
                shipping_crlf = content['shipping'].decode('UTF-8').replace("\r\n", "<br/>")

                # required fields fulfilled, log fields, print ticket

                return render_template("database-job-ticket.html", title="Job Ticket {}".format(new_num),
                                       **content, print_comment=comment_crlf, print_bindery=bindery_crlf,
                                       print_shipping=shipping_crlf)

            except(mysql.connector.Error, mysql.connector.Warning) as e:
                print(e)
                g.user_cnx.rollback()

                cursor.execute("SELECT * FROM edit_ticket WHERE job_number = %s;", (job_number,))
                content = cursor.fetchall()[0]

                cursor.execute('SELECT * FROM top_50_co;')
                comment_crlf = content['comment'].decode('UTF-8').replace("\r\n", "<br/>")
                bindery_crlf = content['bindery'].decode('UTF-8').replace("\r\n", "<br/>")
                shipping_crlf = content['shipping'].decode('UTF-8').replace("\r\n", "<br/>")
                flash(e)
                return render_template("database-new-ticket.html", title="Job Ticket {}".format(job_number),
                                       top_50_co=cursor.fetchall(), print_comment=comment_crlf,
                                       print_bindery=bindery_crlf, print_shipping=shipping_crlf,
                                       action=action, **content)

        if action == 'edit':
            try:
                cursor.execute(("SELECT DATE_FORMAT(order_date,'%Y-%m-%d') as 'order_date' "
                                "FROM ticket_detail WHERE job_number = %s;"), (job_number,))
                order_date = cursor.fetchall()[0]['order_date']

                cursor.execute("DELETE FROM ticket_detail WHERE job_number = %s;", (job_number,))
                # g.user_cnx.commit()

                if usr.get('dueDate') == '':
                    due_date = None
                else:
                    due_date = usr.get('dueDate')

                cmd_ticket_detail = ("insert into ticket_detail values (%s, %s, %s, %s, %s, %s, "
                                     "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
                                     "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
                                     "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
                                     "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);")

                cursor.execute(cmd_ticket_detail, (job_number, usr.get('prevJob'), usr.get('quote'),
                                                   due_date, usr.get('customer', '')[0:65],
                                                   usr.get('jobname', '')[0:65], usr.get('contact', '')[0:40],
                                                   usr.get('commentInput'), usr.get('phone', '')[0:18],
                                                   usr.get('cell', '')[0:18], usr.get('email', '')[0:65],
                                                   usr.get('chkEmail'), usr.get('chkCD'),
                                                   usr.get('chkFTP'), usr.get('otherSource', '')[0:45],
                                                   usr.get('fileName', '')[0:80], usr.get('chkMerge'),
                                                   usr.get('chkDeDupe'), usr.get('chkPresort'),
                                                   usr.get('chkNCOA'), usr.get('chkTNT'),
                                                   usr.get('chkFCM'), usr.get('chkSTD'),
                                                   usr.get('chkNP'), usr.get('chkMeter'),
                                                   usr.get('chkBPM'), usr.get('chkStamp'),
                                                   usr.get('chkPeriodical'), usr.get('chkPostcard'),
                                                   usr.get('chkIndicia'), usr.get('indicia'),
                                                   usr.get('chkMatch'), usr.get('chkCRRT'),
                                                   usr.get('chkListCnt'), usr.get('listCnt'),
                                                   usr.get('chkInkjet'), usr.get('chkLaser'),
                                                   usr.get('chkLabels'), usr.get('chkOutputOther'),
                                                   usr.get('outputOther', '')[0:30], usr.get('jobQty', '')[0:25],
                                                   usr.get('chkFold'), usr.get('chkTab'),
                                                   usr.get('tab', '')[0:1], usr.get('chkInsert'),
                                                   usr.get('insert'), usr.get('chkJumbo'),
                                                   usr.get('chkPoly'), usr.get('chkDuplexColor'),
                                                   usr.get('chkSimplexColor'), usr.get('chkDuplex'),
                                                   usr.get('chkSimplex'), usr.get('stock', '')[0:60],
                                                   order_date, usr.get('rep'), usr.get('binderyInput'),
                                                   usr.get('shippingInput'),
                                                   usr.get('TICKETREF_PLACEHOLDER'),
                                                   usr.get('customerPO', '')[0:20],
                                                   usr.get('linkedBindery')))
                # g.user_cnx.commit()

                sql = ("UPDATE job_detail SET customer = %s, job_name = %s, "
                       "last_edit_ts = TIMESTAMP(NOW()), "
                       "enter_ip = %s "
                       "WHERE job_number = %s;")

                cursor.execute(sql, (usr.get('customer', '')[0:65],
                                     usr.get('jobname', '')[0:65],
                                     request.environ['REMOTE_ADDR'], job_number))
                g.user_cnx.commit()

                cursor.execute("SELECT * FROM select_ticket WHERE job_number = %s;", (job_number,))

                content = cursor.fetchall()[0]
                comment_crlf = content['comment'].decode('UTF-8').replace("\r\n", "<br/>")
                bindery_crlf = content['bindery'].decode('UTF-8').replace("\r\n", "<br/>")
                shipping_crlf = content['shipping'].decode('UTF-8').replace("\r\n", "<br/>")

                # Required fields fulfilled, log fields, print ticket
                return render_template("database-job-ticket.html", title="Job Ticket {}".format(job_number),
                                       **content, print_comment=comment_crlf, print_bindery=bindery_crlf,
                                       print_shipping=shipping_crlf)

            except(mysql.connector.Error, mysql.connector.Warning) as e:
                print(e)
                g.user_cnx.rollback()

                cursor.execute("SELECT * FROM edit_ticket WHERE job_number = %s;", (job_number,))
                content = cursor.fetchall()[0]

                cursor.execute('SELECT * FROM top_50_co;')
                comment_crlf = content['comment'].decode('UTF-8').replace("\r\n", "<br/>")
                bindery_crlf = content['bindery'].decode('UTF-8').replace("\r\n", "<br/>")
                shipping_crlf = content['shipping'].decode('UTF-8').replace("\r\n", "<br/>")
                flash(e)
                return render_template("database-new-ticket.html", title="Job Ticket {}".format(job_number),
                                       top_50_co=cursor.fetchall(),
                                       print_comment=comment_crlf, print_bindery=bindery_crlf,
                                       print_shipping=shipping_crlf, action=action, **content)


@app.route("/new-bindery-ticket/", methods=['GET', 'POST'])
def new_bindery_ticket():
    error = None
    cursor = g.user_cnx.cursor(buffered=True, dictionary=True)
    req_fields = {'customer': None, 'jobname': None}

    try:
        if request.method == 'POST':
            cursor.execute('SELECT * FROM top_50_co;')
            usr = request.form

            if usr.get('inputClearFields') == "":
                return render_template("new-ticket.html", top_50_co=cursor.fetchall(), required=req_fields)

            req_fields['customer'] = usr.get('customer', '')
            req_fields['jobname'] = usr.get('jobname', '')

            if ((req_fields['customer'] == '') or (req_fields['jobname'] == '') or
                    (req_fields['customer'] == 'REQUIRED FIELD') or (req_fields['jobname'] == 'REQUIRED FIELD')):

                # Required fields not filled, try again
                # use edit-ticket.html because it remembers entered fields
                return render_template("edit-ticket.html", top_50_co=cursor.fetchall(), title='New Ticket',
                                       required=req_fields, fields=usr, action=None)
            else:
                try:
                    cursor.execute("SELECT * FROM next_jobnumber;")
                    new_num = cursor.fetchone()['next_num']
                    sql = "insert into job_number  values (%s, timestamp(now()));"
                    cursor.execute(sql, (new_num,))

                    if usr.get('dueDate') == '':
                        due_date = None
                    else:
                        due_date = usr.get('dueDate')

                    cmd_ticket_detail = ("INSERT INTO ticket_detail VALUES (%s, %s, %s, %s, %s, %s, "
                                         "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
                                         "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
                                         "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
                                         "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);")

                    cmd_job_detail = ("INSERT INTO job_detail VALUES (%s, %s, %s, DATE(NOW()), %s, "
                                      "TIME(NOW()), %s, %s, TIMESTAMP(NOW()), %s);")

                    cursor.execute(cmd_job_detail, (new_num, usr.get('customer', '')[0:65],
                                                    usr.get('jobname', '')[0:65],
                                                    None, 1, request.environ['REMOTE_ADDR'], 0))

                    cursor.execute(cmd_ticket_detail, (new_num, usr.get('prevJob'), usr.get('quote'),
                                                       due_date, usr.get('customer', '')[0:65],
                                                       usr.get('jobname', '')[0:65], usr.get('contact', '')[0:40],
                                                       usr.get('commentInput'), usr.get('phone', '')[0:18],
                                                       usr.get('cell', '')[0:18], usr.get('email', '')[0:65],
                                                       usr.get('chkEmail'), usr.get('chkCD'),
                                                       usr.get('chkFTP'), usr.get('otherSource', '')[0:45],
                                                       usr.get('fileName', '')[0:80], usr.get('chkMerge'),
                                                       usr.get('chkDeDupe'), usr.get('chkPresort'),
                                                       usr.get('chkNCOA'), usr.get('chkTNT'),
                                                       usr.get('chkFCM'), usr.get('chkSTD'),
                                                       usr.get('chkNP'), usr.get('chkMeter'),
                                                       usr.get('chkBPM'), usr.get('chkStamp'),
                                                       usr.get('chkPeriodical'), usr.get('chkPostcard'),
                                                       usr.get('chkIndicia'), usr.get('indicia'),
                                                       usr.get('chkMatch'), usr.get('chkCRRT'),
                                                       usr.get('chkListCnt'), usr.get('listCnt'),
                                                       usr.get('chkInkjet'), usr.get('chkLaser'),
                                                       usr.get('chkLabels'), usr.get('chkOutputOther'),
                                                       usr.get('outputOther', '')[0:30], usr.get('jobQty', '')[0:25],
                                                       usr.get('chkFold'), usr.get('chkTab'),
                                                       usr.get('tab', '')[0:1], usr.get('chkInsert'),
                                                       usr.get('insert'), usr.get('chkJumbo'),
                                                       usr.get('chkPoly'), usr.get('chkDuplexColor'),
                                                       usr.get('chkSimplexColor'), usr.get('chkDuplex'),
                                                       usr.get('chkSimplex'), usr.get('stock', '')[0:60],
                                                       dt.datetime.strftime(dt.datetime.now(), "%y-%m-%d"),
                                                       usr.get('rep'), usr.get('binderyInput'),
                                                       usr.get('shippingInput'),
                                                       usr.get('TICKETREF_PLACEHOLDER'),
                                                       usr.get('customerPO', '')[0:20],
                                                       usr.get('linkedBindery')))
                    g.user_cnx.commit()

                    cursor.execute("SELECT * FROM select_ticket WHERE job_number = %s;", (new_num,))

                    content = cursor.fetchall()[0]
                    comment_crlf = content['comment'].decode('UTF-8').replace("\r\n", "<br/>")
                    bindery_crlf = content['bindery'].decode('UTF-8').replace("\r\n", "<br/>")
                    shipping_crlf = content['shipping'].decode('UTF-8').replace("\r\n", "<br/>")

                    # Required fields fulfilled, log fields, print ticket
                    return render_template("database-job-ticket.html", title="Job Ticket {}".format(new_num),
                                           **content, print_comment=comment_crlf, PRINT_BINDERY=bindery_crlf,
                                           print_shipping=shipping_crlf)

                except(mysql.connector.Error, mysql.connector.Warning) as e:
                    print(e)
                    g.user_cnx.rollback()
                    flash(e)
                    cursor.execute('SELECT * FROM top_50_co;')
                    usr = request.form

                    req_fields['customer'] = usr.get('customer', '')
                    req_fields['jobname'] = usr.get('jobname', '')

                    if ((req_fields['customer'] == '') or (req_fields['jobname'] == '') or
                            (req_fields['customer'] == 'REQUIRED FIELD') or (
                                    req_fields['jobname'] == 'REQUIRED FIELD')):
                        # Required fields not filled, try again
                        # use edit-ticket.html because it remembers entered fields
                        return render_template("edit-ticket.html", title='New Ticket',
                                               top_50_co=cursor.fetchall(),
                                               required=req_fields, fields=usr, action=None)

        else:
            # Initial entrance into new ticket page
            cursor.execute('SELECT * FROM top_50_co;')
            return render_template("new-ticket.html", title='New Ticket',
                                   top_50_co=cursor.fetchall(), required=req_fields)

    except Exception as e:
        print('exception')
        print(e)
        flash(e)
        return render_template("new-ticket.html", error=error, required=req_fields)


@app.route("/new-ticket/", methods=['GET', 'POST'])
def new_ticket():
    error = None
    cursor = g.user_cnx.cursor(buffered=True, dictionary=True)
    req_fields = {'customer': None, 'jobname': None}

    try:
        if request.method == 'POST':
            cursor.execute('SELECT * FROM top_50_co;')
            usr = request.form

            if usr.get('inputClearFields') == "":
                return render_template("new-ticket.html", top_50_co=cursor.fetchall(), required=req_fields)

            req_fields['customer'] = usr.get('customer', '')
            req_fields['jobname'] = usr.get('jobname', '')

            if ((req_fields['customer'] == '') or (req_fields['jobname'] == '') or
                    (req_fields['customer'] == 'REQUIRED FIELD') or (req_fields['jobname'] == 'REQUIRED FIELD')):

                # Required fields not filled, try again
                # use edit-ticket.html because it remembers entered fields
                return render_template("edit-ticket.html", top_50_co=cursor.fetchall(), title='New Ticket',
                                       required=req_fields, fields=usr, action=None)
            else:
                try:
                    cursor.execute("SELECT * FROM next_jobnumber;")
                    new_num = cursor.fetchone()['next_num']
                    sql = "insert into job_number  values (%s, timestamp(now()));"
                    cursor.execute(sql, (new_num,))

                    if usr.get('dueDate') == '':
                        due_date = None
                    else:
                        due_date = usr.get('dueDate')

                    cmd_ticket_detail = ("INSERT INTO ticket_detail VALUES (%s, %s, %s, %s, %s, %s, "
                                         "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
                                         "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
                                         "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
                                         "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);")

                    cmd_job_detail = ("INSERT INTO job_detail VALUES (%s, %s, %s, DATE(NOW()), %s, "
                                      "TIME(NOW()), %s, %s, TIMESTAMP(NOW()), %s);")

                    cursor.execute(cmd_job_detail, (new_num, usr.get('customer', '')[0:65],
                                                    usr.get('jobname', '')[0:65],
                                                    None, 1, request.environ['REMOTE_ADDR'], 0))

                    cursor.execute(cmd_ticket_detail, (new_num, usr.get('prevJob'), usr.get('quote'),
                                                       due_date, usr.get('customer', '')[0:65],
                                                       usr.get('jobname', '')[0:65], usr.get('contact', '')[0:40],
                                                       usr.get('commentInput'), usr.get('phone', '')[0:18],
                                                       usr.get('cell', '')[0:18], usr.get('email', '')[0:65],
                                                       usr.get('chkEmail'), usr.get('chkCD'),
                                                       usr.get('chkFTP'), usr.get('otherSource', '')[0:45],
                                                       usr.get('fileName', '')[0:80], usr.get('chkMerge'),
                                                       usr.get('chkDeDupe'), usr.get('chkPresort'),
                                                       usr.get('chkNCOA'), usr.get('chkTNT'),
                                                       usr.get('chkFCM'), usr.get('chkSTD'),
                                                       usr.get('chkNP'), usr.get('chkMeter'),
                                                       usr.get('chkBPM'), usr.get('chkStamp'),
                                                       usr.get('chkPeriodical'), usr.get('chkPostcard'),
                                                       usr.get('chkIndicia'), usr.get('indicia'),
                                                       usr.get('chkMatch'), usr.get('chkCRRT'),
                                                       usr.get('chkListCnt'), usr.get('listCnt'),
                                                       usr.get('chkInkjet'), usr.get('chkLaser'),
                                                       usr.get('chkLabels'), usr.get('chkOutputOther'),
                                                       usr.get('outputOther', '')[0:30], usr.get('jobQty', '')[0:25],
                                                       usr.get('chkFold'), usr.get('chkTab'),
                                                       usr.get('tab', '')[0:1], usr.get('chkInsert'),
                                                       usr.get('insert'), usr.get('chkJumbo'),
                                                       usr.get('chkPoly'), usr.get('chkDuplexColor'),
                                                       usr.get('chkSimplexColor'), usr.get('chkDuplex'),
                                                       usr.get('chkSimplex'), usr.get('stock', '')[0:60],
                                                       dt.datetime.strftime(dt.datetime.now(), "%y-%m-%d"),
                                                       usr.get('rep'), usr.get('binderyInput'),
                                                       usr.get('shippingInput'),
                                                       usr.get('TICKETREF_PLACEHOLDER'),
                                                       usr.get('customerPO', '')[0:20],
                                                       usr.get('linkedBindery')))
                    g.user_cnx.commit()

                    cursor.execute("SELECT * FROM select_ticket WHERE job_number = %s;", (new_num,))

                    content = cursor.fetchall()[0]
                    comment_crlf = content['comment'].decode('UTF-8').replace("\r\n", "<br/>")
                    bindery_crlf = content['bindery'].decode('UTF-8').replace("\r\n", "<br/>")
                    shipping_crlf = content['shipping'].decode('UTF-8').replace("\r\n", "<br/>")

                    # Required fields fulfilled, log fields, print ticket
                    return render_template("database-job-ticket.html", title="Job Ticket {}".format(new_num),
                                           **content, print_comment=comment_crlf, PRINT_BINDERY=bindery_crlf,
                                           print_shipping=shipping_crlf)

                except(mysql.connector.Error, mysql.connector.Warning) as e:
                    print(e)
                    g.user_cnx.rollback()
                    flash(e)
                    cursor.execute('SELECT * FROM top_50_co;')
                    usr = request.form

                    req_fields['customer'] = usr.get('customer', '')
                    req_fields['jobname'] = usr.get('jobname', '')

                    if ((req_fields['customer'] == '') or (req_fields['jobname'] == '') or
                            (req_fields['customer'] == 'REQUIRED FIELD') or (
                                    req_fields['jobname'] == 'REQUIRED FIELD')):
                        # Required fields not filled, try again
                        # use edit-ticket.html because it remembers entered fields
                        return render_template("edit-ticket.html", title='New Ticket',
                                               top_50_co=cursor.fetchall(),
                                               required=req_fields, fields=usr, action=None)

        else:
            # Initial entrance into new ticket page
            cursor.execute('SELECT * FROM top_50_co;')
            return render_template("new-ticket.html", title='New Ticket',
                                   top_50_co=cursor.fetchall(), required=req_fields)

    except Exception as e:
        print('exception')
        print(e)
        flash(e)
        return render_template("new-ticket.html", error=error, required=req_fields)


@app.route("/job-search/", methods=['GET', 'POST'])
def job_search():
    error = None
    try:
        if request.method == 'POST':
            user_input = request.form
            # print(request.values)
            cursor = g.user_cnx.cursor()

            if user_input.get('chkSearchCustomerPO') == 'on':
                sql = ("SELECT a.*, b.customer_po FROM "
                       "full_search AS a JOIN "
                       "ticket_detail AS b ON a.job_number = b.job_number "
                       "WHERE b.customer_po LIKE '%{}%';").format(user_input.get('customer_po'))

                cursor.execute(sql)
                return render_template("search-result.html", title='Search Results',  cursor=cursor.fetchall())

            if user_input.get('chkSearchDateRange') == 'on':
                dates = clean_date_ranges(user_input.get('search_date_start'),
                                          user_input.get('search_date_end'))

                cursor.execute(("SELECT * FROM full_search WHERE create_date"
                                " BETWEEN '{0}' and '{1}'"
                                "ORDER BY create_date;").format(dates['date1'], dates['date2']))

                return render_template("search-result.html", title='Search Results', cursor=cursor.fetchall())

            if user_input.get('chkJobNo') == 'on':
                cursor.execute(("SELECT * FROM full_search WHERE job_number = '{}' "
                                "ORDER BY customer, create_date DESC;".format(user_input.get('jobNumber'))))
                return render_template("search-result.html", title='Search Results', cursor=cursor.fetchall())

            elif user_input.get('chkInvoice') == 'on':
                cursor.execute(("SELECT * FROM full_search WHERE invoice_num = '{}' "
                                "ORDER BY customer, create_date DESC;".format(user_input.get('invoiceNumber'))))
                return render_template("search-result.html", title='Search Results', cursor=cursor.fetchall())

            else:
                if user_input.get('chkDateRange') == 'on':
                    dates = clean_date_ranges(user_input.get('date_start'),
                                              user_input.get('date_end'))

                    date_range = (" AND create_date "
                                  "BETWEEN '{0}' and '{1}' ".format(dates['date1'], dates['date2']))
                else:
                    date_range = ''

                if user_input.get('near_match') == 'on':
                    srch = "WHERE customer LIKE '%{}%' ".format(user_input['customer'])
                else:
                    srch = "WHERE customer = '{}' ".format(user_input['customer'])

                # Last condition separately just so IDE doesn't think there's a SQL statement error
                last_condition = "ORDER BY customer, create_date DESC;"
                cursor.execute("SELECT * FROM full_search " + srch + date_range + last_condition)

                return render_template("search-result.html", title='Search Results', cursor=cursor.fetchall())

        else:
            cursor = g.user_cnx.cursor()
            cursor.execute('SELECT * FROM top_50_co;')
            return render_template("job-search.html", title='Job Search', top_50_co=cursor)

    except Exception as e:
        return render_template("job-search.html", error=error)


def clean_date_ranges(date1, date2):
    if date1 == '':
        date1 = datetime.datetime.today()
    else:
        date1 = datetime.datetime.strptime(date1, "%Y-%m-%d")

    if date2 == '':
        date2 = datetime.datetime.today()
    else:
        date2 = datetime.datetime.strptime(date2, "%Y-%m-%d")

    if date1 < date2:
        dates = {'date1': datetime.datetime.strftime(date1, "%Y-%m-%d"),
                 'date2': datetime.datetime.strftime(date2, "%Y-%m-%d")}
    else:
        dates = {'date2': datetime.datetime.strftime(date1, "%Y-%m-%d"),
                 'date1': datetime.datetime.strftime(date2, "%Y-%m-%d")}
    return dates


@app.route("/request-data/")
def request_data():
    req = request
    print(req.remote_addr)
    return render_template("request-data.html", req=req)


def get_bit(byte_val, idx):
    return byte_val & (1 << idx) != 0


@app.route('/update-status/', defaults={'job_number': None}, methods=['GET', 'POST'])
@app.route('/update-status/<job_number>', methods=['GET', 'POST'])
def update_status(job_number):
    error = 0
    if request.method == 'POST':
        usr = request.form
        cursor = g.user_cnx.cursor(buffered=True, dictionary=True)

        if usr.get('jobnum', '') == '':
            error += 1
        if usr.get('chkCancel', '') == '':
            error += 2
        if usr.get('chkInvoice', '') == '':
            error += 4
        if usr.get('invoiceNumber', '') == '':
            error += 8

        if get_bit(error, 0):
            flash(u'Job Number Field Empty', 'error')
        if not get_bit(error, 0):
            cursor.execute("SELECT * FROM job_detail WHERE job_number = %s;", (usr.get('jobnum', ''),))
            resl = cursor.fetchall()
            # print(error, resl)
            if not resl:
                error += 16
                flash(u'No match for provided job number', 'error')
        if not get_bit(error, 2) and get_bit(error, 3):
            flash(u'Invoice Number Field Empty', 'error')

        # Everything is ok, run the update
        if error == 12 or error == 2:
            if usr.get('chkCancel', '') == '1':
                sql = ("UPDATE job_detail SET  invoice_num = 'CANCELLED', "
                       "last_edit_ts = TIMESTAMP(NOW()), "
                       "enter_ip = %s "
                       "WHERE job_number = %s;")

                cursor.execute(sql, (request.environ['REMOTE_ADDR'], usr.get('jobnum', '')))
                g.user_cnx.commit()

            if usr.get('chkInvoice', '') == '1':
                sql = ("UPDATE job_detail SET  invoice_num = %s, "
                       "last_edit_ts = TIMESTAMP(NOW()), "
                       "enter_ip = %s "
                       "WHERE job_number = %s;")

                cursor.execute(sql, (usr.get('invoiceNumber', ''),
                                     request.environ['REMOTE_ADDR'],
                                     usr.get('jobnum', '')))
                g.user_cnx.commit()

            flash(u'Update complete for job {}'.format(usr.get('jobnum', '')), 'success')
            return render_template("update-status.html", title='Job Update')

    else:
        return render_template("update-status.html", title='Job Update', job_number=job_number)


@app.route("/ticket/<job_number>/")
def ticket_link(job_number):
    cursor = g.user_cnx.cursor(buffered=True, dictionary=True)
    try:
        cursor.execute("SELECT * FROM select_ticket WHERE job_number = %s;", (job_number,))

        content = cursor.fetchall()[0]
        comment_crlf = content['comment'].decode('UTF-8').replace("\r\n", "<br/>")
        bindery_crlf = content['bindery'].decode('UTF-8').replace("\r\n", "<br/>")
        shipping_crlf = content['shipping'].decode('UTF-8').replace("\r\n", "<br/>")

        return render_template("database-job-ticket.html", title="Job Ticket {}".format(job_number), **content,
                               print_comment=comment_crlf, print_bindery=bindery_crlf,
                               print_shipping=shipping_crlf)

    except IndexError as e:
        return render_template("change-log.html", title="Change Log")


@app.route("/job-ticket/")
def job_ticket():
    return render_template("job-ticket.html", title="Job Ticket")


@app.route("/change-log/")
def change_log():
    return render_template("change-log.html", title="Change Log")


@app.route("/quick-search-results/")
def quick_search():
    cursor = g.user_cnx.cursor()
    cursor.execute('SELECT * FROM quick_search;')
    return render_template("quick-search-results.html", title="Recent Job List", cursor=cursor.fetchall())


@app.route("/weather-log/")
def weather_data():
    month_cursor = g.weather_cnx.cursor(buffered=True)
    week_cursor = g.weather_cnx.cursor(buffered=True)

    month_cursor.execute("DELETE FROM log WHERE DATEDIFF(NOW(), logdate) > 45;")
    g.weather_cnx.commit()

    month_cursor.execute('SELECT * FROM month_view;')
    week_cursor.execute('SELECT * FROM week_average;')

    return render_template("weather-log.html", monthview=month_cursor.fetchall(),
                           weekview=week_cursor.fetchall(), title="Weather Data")


if __name__ == '__main__':
    # app.run(host='192.168.0.200', port=5000)
    pass
