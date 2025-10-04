import sys
sys.path.append('scripts')

from models.bas_parser import BASParser
from datetime import datetime

def parse_and_compare():
    parser_partial = BASParser()
    transactions_partial = parser_partial.parse_file('data/Int_pd_other_partial.TXT', None, None)
    
    parser_complete = BASParser()
    transactions_complete = parser_complete.parse_file('data/Int_pd_other_complete.TXT', None, None)
    
    print("=== Parsed Transactions from Partial File (First 6) ===")
    for i, trans in enumerate(transactions_partial[:6], 1):
        print(f"Transaction {i}:")
        print(f"  Responsibility: '{trans['responsibility']}'")
        print(f"  Item (Category): '{trans['item']}'")
        print(f"  Amount (str): '{trans['amount']}'")
        print(f"  Amount (float): {trans['amount']}")
        print(f"  Date: {trans['date']}")
        print(f"  Description: {trans['description']}")
        print(f"  Type: {trans['type']}")
        print("---")
    
    print("\n=== Parsed Transactions from Complete File (First 6) ===")
    for i, trans in enumerate(transactions_complete[:6], 1):
        print(f"Transaction {i}:")
        print(f"  Responsibility: '{trans['responsibility']}'")
        print(f"  Item (Category): '{trans['item']}'")
        print(f"  Amount (str): '{trans['amount']}'")
        print(f"  Amount (float): {trans['amount']}")
        print(f"  Date: {trans['date']}")
        print(f"  Description: {trans['description']}")
        print(f"  Type: {trans['type']}")
        print("---")
    
    print("\n=== Comparison of First 6 Transactions ===")
    identical = True
    for i in range(min(6, len(transactions_partial), len(transactions_complete))):
        partial = transactions_partial[i]
        complete = transactions_complete[i]
        print(f"Transaction {i+1}:")
        resp_match = partial['responsibility'] == complete['responsibility']
        item_match = partial['item'] == complete['item']
        amount_str_match = str(partial['amount']) == str(complete['amount'])
        amount_float_match = abs(partial['amount'] - complete['amount']) < 0.01
        date_match = partial['date'] == complete['date']
        desc_match = partial['description'] == complete['description']
        type_match = partial['type'] == complete['type']
        
        print(f"  Responsibility match: {resp_match} ('{partial['responsibility']}' vs '{complete['responsibility']}')")
        print(f"  Item/Category match: {item_match} ('{partial['item']}' vs '{complete['item']}')")
        print(f"  Amount str match: {amount_str_match} ('{partial['amount']}' vs '{complete['amount']}')")
        print(f"  Amount float match: {amount_float_match} ({partial['amount']} vs {complete['amount']})")
        print(f"  Date match: {date_match} ({partial['date']} vs {complete['date']})")
        print(f"  Description match: {desc_match}")
        print(f"  Type match: {type_match}")
        
        if not all([resp_match, item_match, amount_str_match, amount_float_match, date_match, desc_match, type_match]):
            identical = False
        
        print("---")
    
    print(f"Overall: First 6 transactions {'are identical' if identical else 'have differences'}")

if __name__ == "__main__":
    parse_and_compare()