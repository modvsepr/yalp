#! /usr/bin/env python3
#
# YALP - Yet Another Ledger-cli Parser
#
# vsepr
# Started project on the end of 2024
version = '20250210'
#
# v 20250210
# Cleaned library version
#
# v 20250202
# Added version indication to *_html
#
# v 20250201
# Added more information to balance_html
# Added version indication to *_html
#
# v 20250128
# Added balance_html
#
# v 20250115
# Fixed lack of blank space betweek words in payee
#
# v 20250113
# First working version
#

# Importing the libraries
import os
import sys
import datetime
import numpy as np



def decimal_fix(number):
    '''
    Switch from comma to dots
    :param number:
    :return:
    '''
    number_ = number.split('.')
    if len(number_) > 1:
        number__ = number_[1].split(',')
        number = number_[0] + number__[0] + '.' + number__[1]
    else:
        number__ = number_[0].split(',')
        number = number__[0] + '.' + number__[1]

    return number


def yalp_parser(file):
    '''
    Parse a plain text file in ledger-cli v3 format
    :param file:
    :return:
    '''
    file = open(file, 'r')
    corpus = file.readlines()
    file.close()

    # Parser, no numpy used
    db = []
    account   = []
    commodity = []
    value     = []
    code = ''
    note = ''
    comment = ''
    i = 0
    while i < len(corpus):
        line = corpus[i]
        if len(line.strip()) > 0:
            if '*' in line:
                line = line.split('*')
                flag = '*'
            elif '!' in line:
                line = line.split('!')
                flag = '!'
            else:
                line = line.split()
            # Identifying date
            if len(line[0]) >= 10:
                if line[0][4] == '-' and line[0][7] == '-':
                    date = line[0].strip()
                    # Identifying note
                    if ';' in line[1]:
                        subline = line[1].split(';')
                        note = subline[1].strip()
                    # Identifying code
                    if '(' in line[1]:
                        subline = line[1].split()
                        code = subline[0].strip()
                        subline1 = ' '.join(subline[1:])
                        subline1 = subline1.split(';')
                        payee = subline1[0].strip()
                    else:
                        subline1 = line[1].split(';')
                        payee = subline1[0].strip()
                else:
                    account.append(line[0].strip())
                    commodity.append(line[1].strip())
                    value.append(line[2].strip())
            else:
                # Identifying comment
                if ';' in line[0]:
                    if len(line) > 1:
                        comment = line[1].strip()
        else:
            db.append({
                'date': date,
                'flag': flag,
                'payee': payee,
                'code': code,
                'note': note,
                'comment': comment,
                'account': account,
                'commodity': commodity,
                'value': value
            })
            account = []
            commodity = []
            value = []
            date = ''
            flag = ''
            payee = ''
            code = ''
            note = ''
        i = i + 1

    return db


def yalp_total_account(db, account):
    '''
    Return the total in an account
    :param db:
    :param account:
    :return:
    '''
    total = 0.
    for idb in range(len(db)):
        accounts = db[idb]['account']
        values = db[idb]['value']
        for iac in range(len(accounts)):
            value = values[iac]
            value = float(decimal_fix(value))
            if account in accounts[iac]:
                total = total + value

    return total

def yalp_register_account(db, account):
    '''
    Return the list of transactions in an account
    :param db:
    :param account:
    :return:
    '''
    register = []
    for idb in range(len(db)):
        date = db[idb]['date']
        payee = db[idb]['payee']
        accounts = db[idb]['account']
        values = db[idb]['value']
        for iac in range(len(accounts)):
            value = values[iac]
            # value = float(decimal_fix(value))
            if account in accounts[iac]:
                register.append([date,payee,value])

    return register


def yalp_filter_time(db, start_date, end_date):
    '''
    Return the database filtered by specifica dates
    :param db:
    :param account:
    :return:
    '''
    # for item in db:
    #     print(datetime.datetime.strptime(item['date'], '%Y-%m-%d').date())
    time = [datetime.datetime.strptime(item['date'], '%Y-%m-%d').date() for item in db]
    time = np.array(time)
    interval = np.where((time >= datetime.datetime.strptime(start_date, '%Y-%m-%d').date()) & (
                time <= datetime.datetime.strptime(end_date, '%Y-%m-%d').date()))
    db_filtered = [db[int(d)] for d in interval[0]]

    return db_filtered


def find_all_monday(year):
    mondays = []
    d = datetime.date(year-1, 12, 31)
    d += datetime.timedelta(days=(7 - d.weekday()))  # Move to the first Monday
    while d.year == year:
        # print(d.strftime("%Y-%m-%d"))
        mondays.append(d.strftime('%Y-%m-%d'))
        d += datetime.timedelta(days=7)  # Move to the next Monday

    return mondays


def find_last_monday(day):

    d = datetime.datetime.strptime(day, '%Y-%m-%d').date()
    d += datetime.timedelta(days=(-d.weekday()))
    monday = d.strftime('%Y-%m-%d')

    return monday


def find_last_month_day(day):

    d = datetime.datetime.strptime(day, '%Y-%m-%d').date()
    nxt_mnth = d.replace(day=28) + datetime.timedelta(days=4)
    # subtracting the days from next month date to
    # get last date of current Month
    last_day_mnth = nxt_mnth - datetime.timedelta(days=nxt_mnth.day)
    last = datetime.datetime(d.year, d.month, int(last_day_mnth.day)).strftime('%Y-%m-%d')

    return last


def balance_html(db, html_out, options=[]):
    '''
    Write a balance example into a HTML page

    db: dictionary from yalp_parser
    html_out: string with the name of the output file
    options: [] no options so far
    '''

    # Today
    today = datetime.datetime.today()
    today_date = today.strftime('%Y-%m-%d')

    # Current year
    start_date = datetime.datetime(today.year, 1, 1).strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')


    # BALANCE
    #
    #

    # Search for all the db accounts
    all_accounts = []
    for entry in db:
        for account in entry['account']:
            all_accounts.append(account)
    all_accounts = sorted(list(set(all_accounts)))
    amount = []
    for account in all_accounts:
        if '(' not in account:
            amount.append(yalp_total_account(db, account))
    balance = '{:4.2f}'.format(np.abs(sum(amount)))
    balance = float(balance)

    #
    #
    # #######

    levels_ = []
    for account in all_accounts:
        levels_.append(account.split(':'))
    levels_ = [list(i) for i in zip(*levels_)]
    n_levels = len(levels_[:])
    for il in range(len(levels_[0])):
        for i in range(n_levels):
            if i > 0:
                levels_[i][il] = ':'.join([levels_[i-1][il],levels_[i][il]])
    levels = []
    for i in range(n_levels):
        levels.append(sorted(list(set(levels_[i]))))


    # Print full balance

    # id = 0
    # for i in range(len(levels[-1])):
    #     for account in all_accounts:
    #         if levels[-1][i] in account:
    #             id = id + 1
    #             print(id, i, levels[-1][i], account)
    #     id = id + 1
    #     print(id, i, levels[-1][i])
    stamps = []
    for il in range(len(levels[:])):
        for i in range(len(levels[il])):
            stamps.append(levels[il][i])
    for account in all_accounts:
        stamps.append(account)
    stamps = sorted(list(set(stamps)))
    length = []
    for stamp in stamps:
        length.append(len(stamp.split(':')))
    # Current values
    # expenses = []
    # for account in accounts:
    #     expenses.append(yalp_total_account(db, account))
    amount = []
    amount_today = []
    subdb = yalp_filter_time(db, db[0]['date'], today_date)
    for stamp in stamps:
        amount.append(yalp_total_account(db, stamp))
        amount_today.append(yalp_total_account(subdb, stamp))


    file_index = open(html_out, 'w')

    file_index.write('<html>'+'\n')
    file_index.write('  '+'<head>'+'\n')
    file_index.write('  '+'</head>'+'\n')

    file_index.write('  '+'<body>'+'\n')
    file_index.write('  '+'  '+'<div class=\"top\">Balance</div>'+'\n')
    file_index.write('  '+'  '+'<div class=\"bottop\">'+today.strftime('%Y-%m-%d')+'</div>'+'\n')

    file_index.write('  '+'  '+'<table class=\"nice-table\">'+'\n')
    file_index.write('  '+'  '+'<tr><th>Account</th><th>Current</th><th>Balancing</th></tr>'+'\n')
    for i in range(len(stamps)):
        if np.abs(round(amount[i])) != 0:
            if length[i] == 1:
                if len(stamps[i].split('(')) > 1:
                    stamps[i] = stamps[i].split('(')[-1]
                file_index.write('  '+'  '+'  '+'  '+'<tr><td>'+stamps[i]+'</td><td>'+'{:>10.2f}'.format(float(amount_today[i]))+'</td><td>'+'{:>10.2f}'.format(float(amount[i]))+'</td>'+'\n')
            if length[i] > max(length)-1:
                if len(stamps[i].split(')')) > 1:
                    stamps[i] = stamps[i].split(')')[0]
                file_index.write('  '+'  '+'  '+'  '+'<tr><td>&emsp;&emsp;&emsp;&emsp;'+stamps[i].split(':')[-1]+'</td><td>'+'{:>10.2f}'.format(float(amount_today[i]))+'</td><td>'+'{:>10.2f}'.format(float(amount[i]))+'</td>'+'\n')
    file_index.write('  '+'  '+'  '+'  '+'<tr><td>'+'Balance'+'</td><td></td><td>'+'{:>10.2f}'.format(float(balance))+'</td>'+'\n')
    file_index.write('  '+'  '+'\n')
    file_index.write('  '+'  '+'</table>'+'\n')


    file_index.write('  '+'  '+'<div class=\"bottom\">code v'+version+' printed on '+today.strftime('%Y-%m-%d %H:%M:%S')+'</div>'+'\n')

    file_index.write('  '+'</body>'+'\n')


    file_index.write('  '+'<style>'+'\n')

    file_index.write('  '+'  '+'.top {'+'\n')
    file_index.write('  '+'  '+'  '+'border-collapse: collapse;'+'\n')
    file_index.write('  '+'  '+'  '+'margin: 0 auto;'+'\n')
    # file_index.write('  '+'  '+'  '+'margin: 25px 0;'+'\n')
    file_index.write('  '+'  '+'  '+'font-size: 2em;'+'\n')
    file_index.write('  '+'  '+'  '+'font-family: sans-serif;'+'\n')
    # file_index.write('  '+'  '+'  '+'min-width: 400px;'+'\n')
    file_index.write('  '+'  '+'  '+'width: 90%;'+'\n')
    file_index.write('  '+'  '+'  '+'text-align: center;'+'\n')
    file_index.write('  '+'  '+'}'+'\n')

    file_index.write('  '+'  '+'.bottop {'+'\n')
    file_index.write('  '+'  '+'  '+'border-collapse: collapse;'+'\n')
    file_index.write('  '+'  '+'  '+'margin: 0 auto;'+'\n')
    # file_index.write('  '+'  '+'  '+'margin: 25px 0;'+'\n')
    file_index.write('  '+'  '+'  '+'font-size: 2em;'+'\n')
    file_index.write('  '+'  '+'  '+'font-family: sans-serif;'+'\n')
    # file_index.write('  '+'  '+'  '+'min-width: 400px;'+'\n')
    file_index.write('  '+'  '+'  '+'width: 90%;'+'\n')
    file_index.write('  '+'  '+'  '+'margin-bottom: 2cm;'+'\n')
    file_index.write('  '+'  '+'  '+'text-align: center;'+'\n')
    file_index.write('  '+'  '+'}'+'\n')

    file_index.write('  '+'  '+'.table {'+'\n')
    file_index.write('  '+'  '+'  '+'border-collapse: collapse;'+'\n')
    file_index.write('  '+'  '+'  '+'margin: 0 auto;'+'\n')
    # file_index.write('  '+'  '+'  '+'margin: 25px 0;'+'\n')
    file_index.write('  '+'  '+'  '+'font-size: 1.5em;'+'\n')
    file_index.write('  '+'  '+'  '+'font-family: sans-serif;'+'\n')
    # file_index.write('  '+'  '+'  '+'min-width: 400px;'+'\n')
    file_index.write('  '+'  '+'  '+'width: 90%;'+'\n')
    file_index.write('  '+'  '+'}'+'\n')

    file_index.write('  '+'  '+'.nice-table {'+'\n')
    file_index.write('  '+'  '+'  '+'border-collapse: collapse;'+'\n')
    file_index.write('  '+'  '+'  '+'margin: 0 auto;'+'\n')
    # file_index.write('  '+'  '+'  '+'margin: 25px 0;'+'\n')
    file_index.write('  '+'  '+'  '+'font-size: 1.5em;'+'\n')
    file_index.write('  '+'  '+'  '+'font-family: sans-serif;'+'\n')
    # file_index.write('  '+'  '+'  '+'min-width: 400px;'+'\n')
    file_index.write('  '+'  '+'  '+'width: 90%;'+'\n')
    file_index.write('  '+'  '+'  '+'margin-bottom: 2cm;'+'\n')
    file_index.write('  '+'  '+'  '+'box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);'+'\n')
    file_index.write('  '+'  '+'}'+'\n')

    file_index.write('  '+'  '+'.nice-table th {'+'\n')
    file_index.write('  '+'  '+'  '+'background-color: #009879;'+'\n')
    file_index.write('  '+'  '+'  '+'color: #ffffff;'+'\n')
    file_index.write('  '+'  '+'  '+'text-align: left;'+'\n')
    file_index.write('  '+'  '+'  '+'padding: 12px 15px;'+'\n')
    file_index.write('  '+'  '+'}'+'\n')

    # file_index.write('  '+'  '+'.nice-table th,'+'\n')
    file_index.write('  '+'  '+'.nice-table td {'+'\n')
    file_index.write('  '+'  '+'  '+'padding: 12px 15px;'+'\n')
    file_index.write('  '+'  '+'}'+'\n')

    file_index.write('  '+'  '+'.nice-table tbody tr {'+'\n')
    file_index.write('  '+'  '+'  '+'border-bottom: 1px solid #dddddd;'+'\n')
    file_index.write('  '+'  '+'}'+'\n')

    file_index.write('  '+'  '+'.nice-table tbody tr:nth-of-type(even) {'+'\n')
    file_index.write('  '+'  '+'  '+'background-color: #f3f3f3;'+'\n')
    file_index.write('  '+'  '+'}'+'\n')

    file_index.write('  '+'  '+'.nice-table tbody tr:last-of-type {'+'\n')
    # file_index.write('  '+'  '+'.nice-table tbody tr:nth-last-child(3) {'+'\n')
    file_index.write('  '+'  '+'  '+'border-bottom: 2px solid #009879;'+'\n')
    file_index.write('  '+'  '+'}'+'\n')

    file_index.write('  '+'  '+'.bottom {'+'\n')
    file_index.write('  '+'  '+'  '+'border-collapse: collapse;'+'\n')
    file_index.write('  '+'  '+'  '+'margin: 0 auto;'+'\n')
    # file_index.write('  '+'  '+'  '+'margin: 25px 0;'+'\n')
    file_index.write('  '+'  '+'  '+'font-size: 1em;'+'\n')
    file_index.write('  '+'  '+'  '+'font-family: sans-serif;'+'\n')
    # file_index.write('  '+'  '+'  '+'min-width: 400px;'+'\n')
    file_index.write('  '+'  '+'  '+'width: 90%;'+'\n')
    file_index.write('  '+'  '+'  '+'text-align: left;'+'\n')
    file_index.write('  '+'  '+'  '+'margin-top: 2cm;'+'\n')
    file_index.write('  '+'  '+'  '+'color: gray;'+'\n')
    file_index.write('  '+'  '+'}'+'\n')

    file_index.write('  '+'</style>'+'\n')

    file_index.write('</html>'+'\n')

    file_index.close()

    return


def report_html(db, accounts, html_out, time='week', budget=0., options=[]):
    '''
    Write a report example into a HTML page

    db: dictionary from yalp_parser
    accounts: list of accounts to be included into the html page
    html_out: string with the name of the output file
    time: 'week' or 'month' depending on the periodicity of the report
    budget: 0. if no periodic budget is set and print out the available funds, otherwise your float number
    options: [] no options
             ['periodic_budget'] means the the budget is a budget for your week or month
             ['averages'] print a few annual averages for your reference
             ['periodic_budget', 'averages'] can be combined
    '''

    # Calculate values to show
    today = datetime.datetime.today()

    file_index = open(html_out, 'w')

    file_index.write('<html>'+'\n')
    file_index.write('  '+'<head>'+'\n')
    file_index.write('  '+'  '+'<script type = \"text/javascript\" src = \"https://www.gstatic.com/charts/loader.js\"></script>'+'\n')
    file_index.write('  '+'  '+'<script language = \"JavaScript\">'+'\n')
    file_index.write('  '+'  '+'  '+'google.charts.load(\'current\', {\'packages\': [\'corechart\']});'+'\n')

    # file_index.write('  '+'  '+'  '+'google.charts.setOnLoadCallback(drawTableSummary);'+'\n')
    file_index.write('  '+'  '+'  '+'google.charts.setOnLoadCallback(drawPieWeek);'+'\n')


    if time == 'week':
        # Week interval starting from last Monday
        start_date = find_last_monday(today.strftime('%Y-%m-%d'))
        end_date = (datetime.datetime.strptime(start_date, '%Y-%m-%d') + datetime.timedelta(days=6)).strftime('%Y-%m-%d')
        # All the weeks in the current year
        current_year = int(start_date[0:4])
        mondays_this_year = find_all_monday(current_year)
        saturdays_this_year = []
        for monday in mondays_this_year:
            saturdays_this_year.append((datetime.datetime.strptime(monday, '%Y-%m-%d')+datetime.timedelta(days=6)).strftime('%Y-%m-%d'))
        index = mondays_this_year.index(start_date)
        start_this_year = mondays_this_year[:index]
        end_this_year = saturdays_this_year[:index]
        # All the weeks in the last year
        last_year = int(start_date[0:4])-1
        mondays_last_year = find_all_monday(last_year)
        saturdays_last_year = []
        for monday in mondays_last_year:
            saturdays_last_year.append((datetime.datetime.strptime(monday, '%Y-%m-%d')+datetime.timedelta(days=6)).strftime('%Y-%m-%d'))
        start_last_year = mondays_last_year
        end_last_year = saturdays_last_year

    elif time == 'month':
        # Current month
        start_date = datetime.datetime(today.year, today.month, 1).strftime('%Y-%m-%d')
        end_date = find_last_month_day(today.strftime('%Y-%m-%d'))
        # All the months of the current year
        current_year = int(end_date[0:4])
        current_month = int(end_date[5:7])
        start_this_year = []
        end_this_year = []
        for im in range(1, current_month):
            first_day = str(current_year) + '-' + str(im).rjust(2, '0') + '-01'
            start_this_year.append(first_day)
            end_this_year.append(find_last_month_day(first_day))
        # All the months of the last year
        last_year = int(end_date[0:4])-1
        start_last_year = []
        end_last_year = []
        for im in range(1, 12+1):
            first_day = str(last_year)+'-'+str(im).rjust(2, '0')+'-01'
            start_last_year.append(first_day)
            end_last_year.append(find_last_month_day(first_day))


    # Current values
    subdb = yalp_filter_time(db, start_date, end_date)
    expenses = []
    register = []
    for account in accounts:
        expenses.append(yalp_total_account(subdb, account))
        register_ = yalp_register_account(subdb, account)
        for line in register_:
            line.append(account.split(':')[-1])
            register.append(line)
    register = sorted(register)
    total = sum(expenses)

    # Average values
    if 'averages' in options:
        # This year averages
        expenses_this_year = []
        for account in accounts:
            expenses_this_year_ = 0.
            for ity in range(len(start_this_year)):
                subdb = yalp_filter_time(db, start_this_year[ity], end_this_year[ity])
                expenses_this_year_ = expenses_this_year_ + yalp_total_account(subdb, account)
            if len(start_this_year) > 0.:
                expenses_this_year.append(expenses_this_year_/len(start_this_year))
        total_this_year = sum(expenses_this_year)
        # Last year averages
        expenses_last_year = []
        for account in accounts:
            expenses_last_year_ = 0.
            for ily in range(len(start_last_year)):
                subdb = yalp_filter_time(db, start_last_year[ily], end_last_year[ily])
                expenses_last_year_ = expenses_last_year_ + yalp_total_account(subdb, account)
            expenses_last_year.append(expenses_last_year_/len(start_last_year))
        total_last_year = sum(expenses_last_year)

    file_index.write('  '+'  '+'  '+'function drawPieWeek(){'+'\n')
    file_index.write('  '+'  '+'  '+'  '+'var data = google.visualization.arrayToDataTable(['+'\n')
    file_index.write('  '+'  '+'  '+'  '+'[\'Expenses\', \'Amount\'],'+'\n')
    for i in range(len(accounts)):
        file_index.write('  '+'  '+'  '+'  '+'[\''+accounts[i].split(':')[-1]+'\', '+'{:6.2f}'.format(expenses[i])+'],'+'\n')
    if 'periodic_budget' in options and (total < budget):
        file_index.write('  '+'  '+'  '+'  '+'[\'Available\', '+'{:6.2f}'.format(budget-total)+']'+'\n')
    # else:
    #     file_index.write('  '+'  '+'  '+'  '+'[\' \', '+'{:6.2f}'.format(0)+']'+'\n')
    file_index.write('  '+'  '+'  '+'  '+']);'+'\n')
    file_index.write('  '+'  '+'  '+'  '+ 'var options = {pieHole:0.4,legend:\'none\',fontSize:22,chartArea:{width:\'100%\',left:\'0%\'},pieSliceText:\'label\',slices:{'+'\n')
    file_index.write('  '+'  '+'  '+'  '+'0: { color: \'#66AA00\' },'+'\n')
    file_index.write('  '+'  '+'  '+'  '+'1: { color: \'#5574A6\' },'+'\n')
    file_index.write('  '+'  '+'  '+'  '+'2: { color: \'#E67300\' },'+'\n')
    file_index.write('  '+'  '+'  '+'  '+'3: { color: \'#DD4477\' },'+'\n')
    file_index.write('  '+'  '+'  '+'  '+'4: { color: \'#DC3912\' },'+'\n')
    file_index.write('  '+'  '+'  '+'  '+'5: { color: \'#22AA99\' },'+'\n')
    file_index.write('  '+'  '+'  '+'  '+'6: { color: \'#994499\' },'+'\n')
    file_index.write('  '+'  '+'  '+'  '+'7: { color: \'#0099C6\' },'+'\n')
    file_index.write('  '+'  '+'  '+'  '+str(len(accounts)).strip()+': { color: \'#FFFFFF\' }'+'\n')
    file_index.write('  '+'  '+'  '+'  '+'}};'+'\n')
    file_index.write('  '+'  '+'  '+'  '+'var chart = new google.visualization.PieChart(document.getElementById(\'pieweek_div\'));'+'\n')
    file_index.write('  '+'  '+'  '+'  '+'chart.draw(data, options);'+'\n')
    file_index.write('  '+'  '+'  '+'}'+'\n')

    file_index.write('  '+'  '+'</script>'+'\n')
    file_index.write('  '+'</head>'+'\n')

    file_index.write('  '+'<body>'+'\n')
    # file_index.write('  '+'  '+'<div id = \"chart_div\" style = \"width: 550px; height: 400px; margin: 0 auto\"></div>'+'\n')
    if time == 'week':
        file_index.write('  '+'  '+'<div class=\"top\">Current week</div>'+'\n')
    if time == 'month':
        file_index.write('  '+'  '+'<div class=\"top\">Current month</div>'+'\n')
    file_index.write('  '+'  '+'<div class=\"top\">from '+start_date+' to '+end_date+'</div>'+'\n')
    file_index.write('  '+'  '+'<table class=\"table\">'+'\n')
    file_index.write('  '+'  '+'<tr>'+'\n')
    file_index.write('  '+'  '+'<td><div id = \"pieweek_div\" style=\"height: 800px;\"</div></td>'+'\n')
    file_index.write('  '+'  '+'</tr>'+'\n')
    file_index.write('  '+'  '+'</table>'+'\n')

    # Accounts html table
    if 'averages' in options:
        file_index.write('  '+'  '+'<table class=\"nice-table\">'+'\n')
        file_index.write('  '+'  '+'<tr><th>Expenses</th><th>Amount</th><th>'+str(current_year)+'</th><th>'+str(last_year)+'</th></tr>'+'\n')
        for i in range(len(accounts)):
            try:
                file_index.write(
                    '  ' + '  ' + '  ' + '  ' + '<tr><td>' + accounts[i].split(':')[-1] + '</td><td>' + '{:>10.2f}'.format(
                        float(expenses[i])) + '</td><td>' + '{:>10.2f}'.format(
                        float(expenses_this_year[i])) + '</td><td>' + '{:>10.2f}'.format(
                        float(expenses_last_year[i])) + '</td></tr>' + '\n')
            except:
                file_index.write(
                    '  ' + '  ' + '  ' + '  ' + '<tr><td>' + accounts[i].split(':')[-1] + '</td><td>' + '{:>10.2f}'.format(
                        float(expenses[i])) + '</td><td> </td><td>' + '{:>10.2f}'.format(
                        float(expenses_last_year[i])) + '</td></tr>' + '\n')
        try:
            file_index.write('  ' + '  ' + '  ' + '  ' + '<tr><th>Total amount</th><th>' + '{:>10.2f}'.format(
                float(total)) + '</th><th>' + '{:>10.2f}'.format(
                float(total_this_year)) + '</th><th>' + '{:>10.2f}'.format(
                float(total_last_year)) + '</th></tr>' + '\n')
        except:
            file_index.write('  ' + '  ' + '  ' + '  ' + '<tr><th>Total amount</th><th>' + '{:>10.2f}'.format(
                float(total)) + '</th><th> </th><th>' + '{:>10.2f}'.format(
                float(total_last_year)) + '</th></tr>' + '\n')
        if 'periodic_budget' in options:
            if (total < budget):
                file_index.write('  '+'  '+'  '+'  '+'<tr><td>Available budget</td><td>'+'{:>10.2f}'.format(budget-float(total))+'</td><td></td><td></td></tr>'+'\n')
        else:
            file_index.write('  '+'  '+'  '+'  '+'<tr><td>Available funds</td><td>'+'{:>10.2f}'.format(budget)+'</td><td></td><td></td></tr>'+'\n')
        file_index.write('  '+'  '+'\n')
        file_index.write('  '+'  '+'</table>'+'\n')

    else:
        file_index.write('  '+'  '+'<table class=\"nice-table\">'+'\n')
        file_index.write('  '+'  '+'<tr><th>Expenses</th><th>Amount</th></tr>'+'\n')
        for i in range(len(accounts)):
            file_index.write('  '+'  '+'  '+'  '+'<tr><td>'+accounts[i].split(':')[-1]+'</td><td>'+'{:>10.2f}'.format(float(expenses[i]))+'</td></tr>'+'\n')
        file_index.write('  '+'  '+'  '+'  '+'<tr><th>Total amount</th><th>'+'{:>10.2f}'.format(float(total))+'</th></tr>'+'\n')
        if 'periodic_budget' in options:
            if (total < budget):
                file_index.write('  '+'  '+'  '+'  '+'<tr><td>Available budget</td><td>'+'{:>10.2f}'.format(budget-float(total))+'</td></tr>'+'\n')
        else:
            file_index.write('  '+'  '+'  '+'  '+'<tr><td>Available funds</td><td>'+'{:>10.2f}'.format(budget)+'</td></tr>'+'\n')
        file_index.write('  '+'  '+'\n')
        file_index.write('  '+'  '+'</table>'+'\n')


    file_index.write('  '+'  '+'<table class=\"nice-table\">'+'\n')
    file_index.write('  '+'  '+'<tr><th>Date</th><th>Shop</th><th>Expense</th><th>Amount</th></tr>'+'\n')
    for line in register:
        file_index.write('  '+'  '+'  '+'  '+'<tr><td>'+str(line[0][-5:])+'</td><td>'+str(line[1])+'</td><td>'+str(line[3])+'</td><td>'+'{:>10.2f}'.format(float(decimal_fix(line[2])))+'</td></tr>'+'\n')
    file_index.write('  '+'  '+'\n')
    file_index.write('  '+'  '+'</table>'+'\n')

    file_index.write('  '+'  '+'<div class=\"bottom\">code v'+version+' printed on '+today.strftime('%Y-%m-%d %H:%M:%S')+'</div>'+'\n')

    file_index.write('  '+'</body>'+'\n')

    file_index.write('  '+'<style>'+'\n')

    file_index.write('  '+'  '+'.top {'+'\n')
    file_index.write('  '+'  '+'  '+'border-collapse: collapse;'+'\n')
    file_index.write('  '+'  '+'  '+'margin: 0 auto;'+'\n')
    # file_index.write('  '+'  '+'  '+'margin: 25px 0;'+'\n')
    file_index.write('  '+'  '+'  '+'font-size: 2em;'+'\n')
    file_index.write('  '+'  '+'  '+'font-family: sans-serif;'+'\n')
    # file_index.write('  '+'  '+'  '+'min-width: 400px;'+'\n')
    file_index.write('  '+'  '+'  '+'width: 90%;'+'\n')
    file_index.write('  '+'  '+'  '+'text-align: center;'+'\n')
    file_index.write('  '+'  '+'}'+'\n')

    file_index.write('  '+'  '+'.table {'+'\n')
    file_index.write('  '+'  '+'  '+'border-collapse: collapse;'+'\n')
    file_index.write('  '+'  '+'  '+'margin: 0 auto;'+'\n')
    # file_index.write('  '+'  '+'  '+'margin: 25px 0;'+'\n')
    file_index.write('  '+'  '+'  '+'font-size: 1.5em;'+'\n')
    file_index.write('  '+'  '+'  '+'font-family: sans-serif;'+'\n')
    # file_index.write('  '+'  '+'  '+'min-width: 400px;'+'\n')
    file_index.write('  '+'  '+'  '+'width: 90%;'+'\n')
    file_index.write('  '+'  '+'}'+'\n')

    file_index.write('  '+'  '+'.nice-table {'+'\n')
    file_index.write('  '+'  '+'  '+'border-collapse: collapse;'+'\n')
    file_index.write('  '+'  '+'  '+'margin: 0 auto;'+'\n')
    # file_index.write('  '+'  '+'  '+'margin: 25px 0;'+'\n')
    file_index.write('  '+'  '+'  '+'font-size: 1.5em;'+'\n')
    file_index.write('  '+'  '+'  '+'font-family: sans-serif;'+'\n')
    # file_index.write('  '+'  '+'  '+'min-width: 400px;'+'\n')
    file_index.write('  '+'  '+'  '+'width: 90%;'+'\n')
    file_index.write('  '+'  '+'  '+'margin-bottom: 2cm;'+'\n')
    file_index.write('  '+'  '+'  '+'box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);'+'\n')
    file_index.write('  '+'  '+'}'+'\n')

    file_index.write('  '+'  '+'.nice-table th {'+'\n')
    file_index.write('  '+'  '+'  '+'background-color: #009879;'+'\n')
    file_index.write('  '+'  '+'  '+'color: #ffffff;'+'\n')
    file_index.write('  '+'  '+'  '+'text-align: left;'+'\n')
    file_index.write('  '+'  '+'  '+'padding: 12px 15px;'+'\n')
    file_index.write('  '+'  '+'}'+'\n')

    # file_index.write('  '+'  '+'.nice-table th,'+'\n')
    file_index.write('  '+'  '+'.nice-table td {'+'\n')
    file_index.write('  '+'  '+'  '+'padding: 12px 15px;'+'\n')
    file_index.write('  '+'  '+'}'+'\n')

    file_index.write('  '+'  '+'.nice-table tbody tr {'+'\n')
    file_index.write('  '+'  '+'  '+'border-bottom: 1px solid #dddddd;'+'\n')
    file_index.write('  '+'  '+'}'+'\n')

    file_index.write('  '+'  '+'.nice-table tbody tr:nth-of-type(even) {'+'\n')
    file_index.write('  '+'  '+'  '+'background-color: #f3f3f3;'+'\n')
    file_index.write('  '+'  '+'}'+'\n')

    file_index.write('  '+'  '+'.nice-table tbody tr:last-of-type {'+'\n')
    # file_index.write('  '+'  '+'.nice-table tbody tr:nth-last-child(3) {'+'\n')
    file_index.write('  '+'  '+'  '+'border-bottom: 2px solid #009879;'+'\n')
    file_index.write('  '+'  '+'}'+'\n')

    # file_index.write('  '+'  '+'.nice-table tbody td:last-child {'+'\n')
    # file_index.write('  '+'  '+'  '+'text-align: right;'+'\n')
    # file_index.write('  '+'  '+'}'+'\n')

    file_index.write('  '+'  '+'.bottom {'+'\n')
    file_index.write('  '+'  '+'  '+'border-collapse: collapse;'+'\n')
    file_index.write('  '+'  '+'  '+'margin: 0 auto;'+'\n')
    # file_index.write('  '+'  '+'  '+'margin: 25px 0;'+'\n')
    file_index.write('  '+'  '+'  '+'font-size: 1em;'+'\n')
    file_index.write('  '+'  '+'  '+'font-family: sans-serif;'+'\n')
    # file_index.write('  '+'  '+'  '+'min-width: 400px;'+'\n')
    file_index.write('  '+'  '+'  '+'width: 90%;'+'\n')
    file_index.write('  '+'  '+'  '+'text-align: left;'+'\n')
    file_index.write('  '+'  '+'  '+'margin-top: 2cm;'+'\n')
    file_index.write('  '+'  '+'  '+'color: gray;'+'\n')
    file_index.write('  '+'  '+'}'+'\n')

    file_index.write('  '+'</style>'+'\n')

    file_index.write('</html>'+'\n')

    file_index.close()

    return


# ---------------------------------------------------------------------


def main():

    print('Call yalp into your code using the importing command:')
    print('from yalp import *')
    print('')
    print('Update the example.ledger file and uncomment the lines to write the report file.')

    # Example report and balance
    #
    # folder_in = './example/'
    # ledger_filename = 'example.ledger'
    # db = yalp_parser(folder_in+ledger_filename)
    #
    # budget = 240. # EUR
    # period = 'month'
    # folder_out = './example/'
    # html_filename = 'myreport.html'
    # accounts = ['Expenses:Food', 'Expenses:Gas', 'Expenses:Restaurant']
    # report_html(db, accounts, folder_out+html_filename, period, budget, options=['periodic_budget','averages'])
    # html_balance = 'mybalance.html'
    # balance_html(db, folder_out+html_balance)




if __name__ == '__main__':

    main()
