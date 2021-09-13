import os
from dataclasses import dataclass
from abc import ABC, abstractmethod
import datetime
import json 
import pandas as pd
import numpy as np
import pytz


class Bill(ABC):
    """"Represents a generic bill class"""
    @abstractmethod
    def set_up(self) -> None:
        """returns the create output of  Bill class"""


class GenerateStatus:
    def __init__(self, path='../db/', bill_name='investor.json'):
        self.path = path
        self.bill_name = bill_name
    def show_list(self):
        """Generates a random email send status and paid status"""
        df_investor = pd.read_json(self.path+self.bill_name)
        temp = df_investor.drop(columns=['phone', 'adress'])
        df_investor = temp
        df_investor["email_send"] = np.random.choice([True, False], size=len(df_investor))
        df_investor["invoice_status"] = np.random.choice(["paid", "overdue"], size=len(df_investor))
        return df_investor

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
    def __init__(self, bill,bill_name, path, path_grouped='../db/grouped/'):
        self.bill = bill
        self.path = path
        self.path_grouped  = path_grouped
        self.bill_name = bill_name
    def generate_bill(self, group_option=False):
        self.bill['id'] = [x for x in range(1, len(self.bill.values)+1)]
        # arrange the columns of the df
        if 'status' in self.bill.columns:
            self.bill = self.bill[['id','investor_id', 'investment_id', 'fees_amount', 'date_added', 'fees_type', 'status' ]]
        else:
            self.bill = self.bill[['id','investor_id', 'investment_id', 'fees_amount', 'date_added', 'fees_type' ]]
        if not group_option:
            self.bill.to_json(self.path +f'{self.bill_name}.json',orient='records', indent=4)
            self.bill.to_csv(self.path+ f'{self.bill_name}.csv', index=True)
        else:
            gk = self.bill.sort_values(by=['investor_id'])
            for i in range(1,21):
                subset = gk.loc[gk['investor_id'] == i ]
                subset.to_json(f'{self.path_grouped}bill_investor_id_{i}.json', orient='records',indent =4)
                subset.to_csv(f'{self.path_grouped}bill_investor_id_{i}.csv', index=True)

class GroupBills:
    def __init__(self, path, grouped_path):
        self.path = path
        self.grouped_path = grouped_path
    def merge_bills(self):
        dir_content = os.listdir(self.path)
        path_dir_content = [os.path.join(self.path, doc) for doc in dir_content]
        docs = [doc for doc in path_dir_content if os.path.isfile(doc)]
        result = {}
        for doc in docs:
            full_doc_path, filetype = os.path.splitext(doc)
            if filetype.endswith('.json'):
                doc_name = os.path.basename(full_doc_path)
                id_send = doc_name.rsplit('_',1)[1]
                result[id_send] = []
                with open(doc, 'r') as infile:
                    result[id_send].append(json.load(infile))

        with open(f'{self.grouped_path}bills_grouped.json', 'w') as output_file:
            json.dump(result, output_file, indent=4)

class Validate:
    def __init__(self, list_ids, bill):
        self.list_ids = list_ids
        self.bill = bill
    def validate(self):
        for lists in self.list_ids:
            try:
                self.bill.drop(self.bill[(self.bill.investor_id == int(lists[0])) \
                    & (self.bill.investment_id == int(lists[1]))].index, inplace=True)
                print(f"succesfully dropped investor_id: {lists[0]} & investment_id : {lists[1]}")
            except:
                print('could not find the id pair ')
        self.bill['status'] ='validated'
        return self.bill

class GenerateTempBill:
    def __init__(self, bill, bill_name, path,):
        self.bill = bill
        self.bill_name = bill_name
        self.path = path
    def generate(self):
        temp = self.bill.drop(columns=['investment_id', 'fees_type', 'invested_ammount'])
        self.bill = temp
        grouped = self.bill.groupby('investor_id').agg({
            'fees_amount': sum,
            'status': 'first',
            'date_added': min,
        })
        grouped.to_json(self.path +f'{self.bill_name}.json',orient='records', indent=4)
        grouped.to_csv(self.path+ f'{self.bill_name}.csv', index=True)
        return grouped

class CashCall:
    def __init__(self, first_bill, second_bill, bill_name, path):
        self.first_bill = first_bill
        self.second_bill = second_bill
        self.bill_name = bill_name
        self.path = path
    def generate(self):
        """generates the cash call from the bills"""
        df_temp = pd.merge( self.first_bill , self.second_bill, how="inner", left_on="investor_id", right_on="id")
        columns_to_drop = ["name", "email", "status"]
        df_new = df_temp.drop(columns=columns_to_drop)
        df_new = df_new.rename(columns={'credit': 'IBAN', 'fees_amount' : 'total_amount', 'invoice_status': 'Invoice_status'} )
        df_new = df_new[['id', 'total_amount', 'IBAN', 'email_send', 'date_added', 'Invoice_status']]
        df_new.to_json(f'{self.path}cash_call.json', orient='records',indent =4)
        df_new.to_csv(f'{self.path}cash_call.csv', index =True)
        return df_new

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
        print(result_bill.head(3))
        groupby_option = input("Do you want to group by investor ? [y/n]: ").upper()
        if groupby_option == 'Y':
            GenerateBill(result_bill,'bills', '../db/', '../db/grouped/').generate_bill(True)
            GroupBills('../db/grouped/', '../db/').merge_bills()
        elif groupby_option == 'N':
            GenerateBill(result_bill,'bills', '../db/').generate_bill()
        else:
            raise Exception("Sorry can\'t understand the option")
        print('Next step is validation...(using bills.json)')
        ans = input('Ready to drop data which are not validate? [y/n]:').upper()
        send_ids =[]
        while ans == 'Y':
            pair_ids = str(input("Enter the investor id/investment id pair which is not validated  and will be removed [investor_id,investment_id]: "))
            list_ids = pair_ids.split(",")
            try:
                send_ids.append(list_ids)
            except:
                print('Cannot read the option provided')
            ans = input('Continue with validating more ( add more id pairs ) [y/n] ?').upper()
        validated_bill = Validate(send_ids, result_bill).validate()
        GenerateBill(validated_bill, 'validated_bills','../db/').generate_bill()
        temp_bill = GenerateTempBill(validated_bill,'temp_bill', '../db/').generate()
        print("Generating a random email status list and random paid response list...")
        status = GenerateStatus().show_list()
        print(status)
        print("Generating cash call....")
        cash_call = CashCall(temp_bill, status, 'cash_call','../db/' ).generate()
        print(cash_call.head(2))


if __name__ =="__main__":
    main()