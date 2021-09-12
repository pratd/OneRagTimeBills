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
import pytz

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
            proceed = input("Do you want to keep going? [y/n]").upper()
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

    def set_up(self, cutoff_date='2019-04-01', membership_fees=3000, cutoff_limit=50000):
        # calculating the bills
        # taking care of the yearly membership fees
        conditions_member =[(self.bill['invested_ammount'] <= cutoff_limit), \
            (self.bill['invested_ammount'] > cutoff_limit)]
        values_member = [membership_fees, 0]
        self.bill['membership_fees'] = np.select(conditions_member, values_member)
        # calculating the yearly and upfront fees
        """To account for changes in way memebership is caculated yearly we append to conditions"""
        conditions_date = []
        conditions_date = [(self.bill['date_added'] > cutoff_date)
                    & (self.bill['fees_type'] == 'yearly'),
                    (self.bill['date_added'] < cutoff_date) 
                    & (self.bill['fees_type'] == 'yearly')]
        values_cutoff=[1,0]
        self.bill['date_cat_hot_new'] = np.select(conditions_date,values_cutoff, default=0)
        values_cutoff =[0,1]
        self.bill['date_cat_hot_old'] = np.select(conditions_date,values_cutoff, default=0)
        # generating a one hot encoder based on fees type
        condition_fees = [(self.bill['fees_type'] == 'yearly'), (self.bill['fees_type']=='upfront')]
        value_fees = [1,0]
        self.bill['one_hot_fees_yearly'] = np.select(condition_fees,value_fees, default=0)
        value_fees = [0,1]
        self.bill['one_hot_fees_upfront'] = np.select(condition_fees,value_fees, default=0)
        # calculating the upfront fees
        self.bill['upfront_fees'] = self.bill['one_hot_fees_upfront'] * \
            self.bill['percentage_fees'] /100 * self.bill['invested_ammount'] * 5
        # calculating the yearly fees
        self.bill['date_diff'] = ((datetime.datetime.now(tz=pytz.UTC)\
            -self.bill['date_added'].apply(pd.to_datetime)).astype('timedelta64[D]') // (365.25)).astype(int)
        conditions_first_yearly = [( self.bill['date_diff'] >= 0)\
            & (self.bill['fees_type'] == 'yearly')]
        conditions_second_yearly = [( self.bill['date_diff'] >= 1)\
            & (self.bill['fees_type'] == 'yearly')]
        conditions_third_yearly = [( self.bill['date_diff'] >= 2)\
            & (self.bill['fees_type'] == 'yearly')]
        conditions_fourth_yearly = [( self.bill['date_diff'] >= 3)\
            & (self.bill['fees_type'] == 'yearly')]
        conditions_following_yearly = [( self.bill['date_diff'] >= 4)\
            & (self.bill['fees_type'] == 'yearly')]
        values_first_year = [1]
        values_second_year = [1]
        values_third_year = [1]
        values_fourth_year = [1]
        values_following_year = [1]
        self.bill['one_hot_first_year'] = np.select(conditions_first_yearly, values_first_year, default=0)
        self.bill['one_hot_second_year'] = np.select(conditions_second_yearly, values_second_year, default=0)
        self.bill['one_hot_third_year'] = np.select(conditions_third_yearly, values_third_year, default=0)
        self.bill['one_hot_fourth_year'] = np.select(conditions_fourth_yearly, values_fourth_year, default=0)
        self.bill['one_hot_subsequent_year'] = np.select(conditions_following_yearly, values_following_year, default=0)
        self.bill['years'] = (self.bill['date_added'].apply(pd.to_datetime)).values.astype('datetime64[Y]').astype(int) + 1970
        self.bill['leap_year'] = [366 if ( (year % 4 == 0) and (year % 100 !=0 and year % 400 ==0)) else 365 for year in self.bill['years']]
        #First year fees
        self.bill['first_year_fees'] =  self.bill['one_hot_first_year'] * (
            (self.bill['date_cat_hot_old'] *
            self.bill['date_added'].str.slice(8,10).astype(int) / 365
            * self.bill['percentage_fees'] /100 * self.bill['invested_ammount'] )+
           (self.bill['date_cat_hot_new'] *
            self.bill['date_added'].str.slice(8,10).astype(int) / self.bill['leap_year']
        * self.bill['percentage_fees'] /100 * self.bill['invested_ammount'])
            )
        # second year fees
        self.bill['second_year_fees'] =  self.bill['one_hot_second_year'] * (
            (self.bill['date_cat_hot_old'] 
            * self.bill['percentage_fees'] /100 * self.bill['invested_ammount'] )+
            (self.bill['date_cat_hot_new'] *
            self.bill['percentage_fees'] /100 * self.bill['invested_ammount'])
            )
        # third year fees
        self.bill['third_year_fees'] =  self.bill['one_hot_third_year'] * (
            ( self.bill['date_cat_hot_old'] 
            * self.bill['percentage_fees'] /100 * self.bill['invested_ammount'] ) +
            (self.bill['date_cat_hot_new'] *
            (self.bill['percentage_fees'] -2)/100 * self.bill['invested_ammount'])
            )
        # fourth year fees
        self.bill['fourth_year_fees'] =  self.bill['one_hot_fourth_year'] * (
            ( self.bill['date_cat_hot_old'] 
            * self.bill['percentage_fees'] /100 * self.bill['invested_ammount'] ) +
            (self.bill['date_cat_hot_new'] *
            (self.bill['percentage_fees'] -5)/100 * self.bill['invested_ammount'])
            )
        # following year fees
        self.bill['following_year_fees'] =  self.bill['one_hot_subsequent_year'] * (
            ( self.bill['date_cat_hot_old'] 
            * self.bill['percentage_fees'] /100 * self.bill['invested_ammount'] ) +
            (self.bill['date_cat_hot_new'] *
            (self.bill['percentage_fees'] -10)/100 * self.bill['invested_ammount'])
            )
        self.bill['fees_amount'] = (self.bill['membership_fees'] + self.bill['upfront_fees'] + \
        self.bill['first_year_fees'] + self.bill['second_year_fees'] + \
        self.bill['third_year_fees'] + self.bill['fourth_year_fees'] + \
        self.bill['following_year_fees']).astype(int)
        drop_cols = ['percentage_fees', 'membership_fees', 'date_cat_hot_new', 'date_cat_hot_old',
                    'one_hot_fees_yearly', 'one_hot_fees_upfront', 'upfront_fees', 'date_diff',
                    'one_hot_first_year', 'one_hot_second_year', 'one_hot_third_year',
                    'one_hot_fourth_year', 'one_hot_subsequent_year', 'years', 'leap_year',
                    'first_year_fees', 'second_year_fees', 'third_year_fees',
                    'fourth_year_fees', 'following_year_fees', 'name' ]
        temp = self.bill.drop(columns = drop_cols)
        self.bill = temp
        return self.bill

class GenerateBill:
    def __init__(self, bill ) -> None:
        self.bill = bill
    def generate_bill(self, group_option=False):
        self.bill['id'] = [x for x in range(1, len(self.bill.values)+1)]
        # arrange the columns of the df
        self.bill = self.bill[['id','investor_id', 'investment_id', 'fees_amount', 'date_added', 'fees_type' ]]
        if not group_option:
            self.bill.to_json('../db/bills.json',orient='records', indent=4)
        else:
            gk = self.bill.groupby(['investor_id'])
            gk.to_json('../db/bills_grouped.json',orient='records', indent=4)


def main()->None:
    """Main function"""

    select_ans = input("Ready to Create a new bill? [y/n] : ").upper()
    if select_ans =="Y" :
        temp_file = SetUpBill(investor_path="../db/investor.json", investment_path="../db/investments.json").set_up()
        # create the bill from the temp dataframe that has been created
        new_bill = ManipulateBill(temp_file)
        ans = input("Do you want to change settings for membership fees calculation ? [y/n] : ").upper()
        if ans == "Y":
            date_list = input("Enter new cutoff date for membership calculation *yyyy-mm-dd  : ")
            fees = input("Enter the new yearly memebrship fee [0 if changed to 0 memebership fee]:")
            fees_cutoff = input("Enter new membership cutoff investment limit [ 0 if no membership fees]: ")
            if date_list and fees and fees_cutoff:
                result_bill = new_bill.set_up(date_list, int(fees), int(fees_cutoff))
            else:
                raise Exception("Sorry can\'t understand the options")
        else:
            result_bill = new_bill.set_up()
        groupby_option = input("Do you want to group by investor ? [y/n]: ").upper()
        if groupby_option == 'Y':
            GenerateBill(result_bill).generate_bill(True)
        elif groupby_option == 'N':
            GenerateBill(result_bill).generate_bill()
        else:
            raise Exception("Sorry can\'t understand the option")
       
       
       
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