import os
import argparse
from dataclasses import dataclass
from abc import ABC, abstractmethod
import datetime
from sre_constants import ANY_ALL
from typing import Optional
import json 
from re import search, IGNORECASE
import pandas as pd
import numpy as np


class Input(ABC):
    """Represents a generic create class"""
    @abstractmethod
    def set_input(self):
        """returns the user request"""
    @abstractmethod
    def is_ready(self) -> bool:
        """checks for user continous action"""

class Bill(ABC):
    """"Represents a generic bill class"""
    @abstractmethod
    def set_up(self) -> None:
        """returns the create output of  Bill class"""



class Proceed(Input):
    def __init__(self):
        self.ready = None
    def set_input(self):
        proceed = ""
        while proceed != "N" :
            proceed = input("Do you want to keep going? [y/Y/n/N]").upper()
            if proceed != "Y" and proceed != "N":
                self.ready = proceed == "N"
                return
        self.ready = proceed == "N"
    def is_ready(self) -> bool:
        return self.ready

class AddBill:
    def __init__(self, ready):
        self.ready = ready
    def create_bill(self):
        pass

class ShowList:
    def show_list(self):
        path = '../db/'
        with open(path+'investor.json') as json_file:
            data = json.load(json_file)
            for p in data:
                identifier = p["id"]
                investor_name = p["name"]
                print(f"Investor id : {identifier}, name : {investor_name}")
                print('')

class SearchListInvestor:
    def __init__(self, word) -> None:
        self.name = word

    def search_list(self):
        path = '../db/'
        with open(path+'investor.json') as json_file:
            data = json.load(json_file)
            all_results = []
            for p in data:
                temp = search(self.name, p["name"], IGNORECASE )
                if temp:
                    send_data = {}
                    send_data["investor_id"] = p["id"]
                    send_data["name"] = p["name"]
                    send_data["email"] = p["email"]
                    all_results.append(send_data)
            if len(all_results) >= 1:
                print("These are all the investors details based on your search")
            else:
                print("No investor found, try again!")
            return all_results

class SearchListInvestment:
    def __init__(self, investor_id) -> None:
        self.investor_id = investor_id

    def search_list(self):
        path = '../db/'
        with open(path+'investments.json') as json_file:
            data = json.load(json_file)
            all_results = []
            for p in data:
                if p["investor_id"] == self.investor_id:
                    send_data = {}
                    send_data["investment_id"] = p["id"]
                    send_data["invested_ammount"] = p["invested_ammount"]
                    send_data["percentage_fees"] = p["percentage_fees"]
                    send_data["date_added"] = p["date_added"]
                    send_data["fees_type"] = p["fees_type"]
                    all_results.append(send_data)
            if len(all_results) >= 1:
                print("These are all the investment details based on your search")
            else:
                print("No investment details found, please try again!")
            return all_results

@dataclass
class SetUpBill(Bill):
    """Basic representation of a Bill """
    investor_path : str
    investment_path : str
    def set_up(self):
        """Sets up the Bill """
        try:
            df_investor = pd.read_json(self.investor_path)
            df_investment = pd.read_json(self.investment_path)
            # doing inner join on investor id to get all data
            df_temp = pd.merge(df_investor, df_investment, how="inner", left_on="id", right_on="investor_id")
            # columns = list(df_temp.columns.values)
            # dropping columns not needed
            columns_to_drop = ["id_x", "adress", "credit", "phone", "startup_name", "email"]
            df_new = df_temp.drop(columns=columns_to_drop)
            df_new = df_new.rename(columns={'id_y': 'investment_id'} )
            return df_new
        except NameError:
            print("Error: File path not found")


class ManipulateBill(Bill):
    def __init__(self, bill ) -> None:
        self.bill = bill

    def set_up(self, cutoff_date=['2019-04-01']):
        # temp = df_new.to_json(orient="records")
        # parsed = json.loads(temp)
        # printed = json.dumps(parsed, indent=4)
        # calculating the bills
        """To account for changes in way memebership is cakculated yearly we append to conditions"""
        conditions = []
        values = ['tier_0']
        for index, date in enumerate(cutoff_date):
            if index == 0 and  len(cutoff_date) > 1:
                temp = [(self.bill['date_added'] < date)
                            & (self.bill['fees_type'] == 'yearly')]
            elif index >= 0 and ( index < len(cutoff_date) or len(cutoff_date)==1):
                temp = [(self.bill['date_added'] > date)
                            & (self.bill['fees_type'] == 'yearly'),
                            (self.bill['date_added'] < date) 
                            & (self.bill['fees_type'] == 'yearly')]
            else:
                temp =[(self.bill['date_added'] > date)
                            & (self.bill['fees_type'] == 'yearly')]
            conditions  += temp
            values.append(f'tier_{index+1}')
        self.bill['temp'] = np.select(conditions,values, default='tier_n')
        return self.bill

def main()->None:
    """Main function"""

    select_ans = input("Ready to Create a new bill? [y/n] : ").upper()
    if select_ans =="Y" :
        temp_file = SetUpBill(investor_path="../db/investor.json", investment_path="../db/investments.json").set_up()
        # create the bill from the temp dataframe that has been created
        new_bill = ManipulateBill(temp_file)
        ans = input("Do you want to change settings for membership fees calculation ? [y/n]").upper()
        if ans == "Y":
            date_list = input("Enter cutoff date/s for membership calculation *yyyy-mm-dd [ Note: if multiple dates, use comma separtor and start from initial cutoffs] : ")
            if date_list:
                date_list = date_list.split(",") 
                temp_bill = new_bill.set_up(date_list)
            else:
                raise Exception("Sorry can\'t understand the options")
        else:
            temp_bill = new_bill.set_up()
        print(temp_bill)
        investor_select = input("Do you know the investor id/name? [y/n] : " ).upper()
        if investor_select == "N":
            print("\n Showing the investor list... \n")
            ShowList().show_list()
        elif  investor_select != "N" and investor_select != "Y" :
            print('\n Can\'t understand the options. Please try again')
        option_selected = input("Choose option to Enter; 1. investor\'s name (partial is good) or 2. id? [1/2] ): ")
        if option_selected == "1":
            investor_selected = input("Enter investor\'s name (partial is good): ")
            investor_detail = SearchListInvestor(investor_selected).search_list()
            if len(investor_detail) >= 1:
                print(investor_detail)
                investor_id = int(input("Choose among the investor ids : "))
            else:
                investor_id= None
        else:
            investor_id = int(input("Enter investor\'s id? ): "))
        investment_details = ''
        print(investor_id)
        if investor_id != None:
            investment_details = SearchListInvestment(investor_id).search_list()
        print(investment_details)
        # finally using the investment and investor id to add billing information
        if len(investment_details) >=1:
            investment_ids_list = input("Choose the list of investments based on ids (with space separator) : ")
            
        # Proceed().set_input()
    elif select_ans == "N":
        print("Exiting.." )
        return
    else:
        print('\n Can\'t understand the options. Please try again')
        return
    Proceed().set_input()


if __name__ =="__main__":
    main()