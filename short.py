import requests
import math
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

TMP_STOCK_PRICE_CHANGE = 0

def retrieveCompanyList(soup):
    companyList = []
    countryList = []
    for a in soup.find_all('a', {"class" : "ellipsis"} , href=True):
        indexBeforeCountryName = str(a).index("flag small ") + 11
        indexAfterCountryName = indexBeforeCountryName + 2
        country = str(a)[indexBeforeCountryName:indexAfterCountryName]
        countryList.append(country)

        indexBeforeCompanyName = str(a).index("></span>") + 8
        indexAfterCompanyName = str(a).index("\r\n\t")
        company = str(a)[indexBeforeCompanyName:indexAfterCompanyName]
        companyList.append(company[0:25])

    return companyList, countryList

def retrieveStockData(soup, countryList):
    rowList = []
    X_dag = []
    Utd_dag = []
    Utdelning = []
    Owners = []
    procentUtd = []
    table = soup.find("div", {'class': "tableScrollContainer"})
    for row in table.findAll("span"):
        row = str(row).replace("\n","")
        #row = row[:row.index("<\span>")]
        if row == " " or row == "\n" or row == "\\n":
            continue
        else:
            row = row.split()[1:3]
            rowList.append(row)

    # Retrieves the stock data and converts it better form
    i = 0
    for x in rowList:
        if i == 3 or i == 4:
            i += 1
            continue
        elif i == 0:
            X_dag.append(x[0])
            i += 1
            continue
        elif i == 1:
            Utd_dag.append(x[0])
            i += 1
            continue
        elif i == 2:
            x = x[0].replace(",", ".")
            x = float(x)
            x = round(x, 2)
            Utdelning.append(x)
            i += 1
            continue
        elif i == 5:
            if x[1] == '</span>':
                x = int(x[0])
                Owners.append(x)
                i += 1
                continue
            else:
                x = ''.join(x)
                x = int(x)
                Owners.append(x)
                i += 1
                continue
        i = 0

    # Retrieves the stock price and converts it better form
    stockPrice = []
    for row in soup.findAll("span", {'class': "pushBox"}):
        row = str(row)
        index = row.index("</span")
        row = row[index-60:]
        row = row[:10]
        price = []
        for x in list(row):
            if x == '\r' or x == '\n' or x == ' ' or x == '\t':
                continue
            else:
                price.append(x)
        price = float(''.join(price).replace(',','.'))
        stockPrice.append(price)

    for i in range(0, len(countryList)):
        procent = round((Utdelning[i] / stockPrice[i]) * 100, 2)
        procentUtd.append(procent)

    data = {
        "Land": countryList,
        "X-dag": X_dag,
        "Utdelningsdag": Utd_dag,
        "Utdelning": Utdelning,
        "Kurs": stockPrice,
        "% Utdel.": procentUtd,
        "Ägare": Owners
    }

    return data

def findShortStocks(df):
    df = df.loc[df['Land'] == 'SE']
    df = df.loc[df['Ägare'] > 25000]
    df = df.loc[df['% Utdel.'] > 2]
    print(df)
    return(df)

def outputFiles(df, bool):
    #df.to_csv('out.csv')
    df.to_csv('/var/www/html/out.csv')
    print("Successfully wrote to out.csv \n")
    with open("log.txt", "a") as myfile:
        dt = datetime.now()
        myfile.write("Wrote to CSV file at: " + str(dt) + "\n")
        if bool == True:
            myfile.write("Made trade and changed wallet balance at: " + str(dt) + "\n")
        
def walletTrade(df):
    with open("out.csv", "r") as myfile:
        lines = myfile.read().split("\n")
        for i, line in enumerate(lines):
            company = line.split(",")[0]
            if company == str(df.index[i-1]):
                oldStockPrice = float(line.split(',')[5])
                newStockPrice = float(df['Kurs'].iloc[0])
                change = abs(1 - (newStockPrice / oldStockPrice))
                with open("/var/www/html/wallet.txt","r+") as thisfile:
                    balance = int(thisfile.read())
                    diffBalance = int(round(balance * change))
                    if change < 1:
                        total = balance + diffBalance
                        thisfile.seek(0)
                        thisfile.write(str(total))
                        thisfile.truncate()
                        return
                    elif change > 1:
                        thisfile.wr
                        total = balance - diffBalance
                        thisfile.seek(0)
                        thisfile.write(str(total))
                        thisfile.truncate()
                        return

if __name__ == "__main__":
    URL = "https://www.avanza.se/aktier/topplistor.html/dJntxqDZ"
    page = requests.get(URL)
    data = page.text
    soup = BeautifulSoup(data, "html.parser")
    companies, countries = retrieveCompanyList(soup)
    stockData = retrieveStockData(soup, countries)

    # Generating Dataframe
    df = pd.DataFrame(stockData, companies)
    stockToShort = findShortStocks(df)

    if str(stockToShort['X-dag'].iloc[0]) == str(str(datetime.now()).split(" ")[0]):
        trade = walletTrade(stockToShort)
        outputFiles(stockToShort, True)

    else:
        #print("done")
        outputFiles(stockToShort, False)
