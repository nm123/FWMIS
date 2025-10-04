import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.models.bas_parser import BASParser

parser = BASParser()
transactions = parser.parse_file('data/Int_pd_other_partial.TXT', None, None)

print("Parsed transactions from partial file:")
for i, trans in enumerate(transactions[:6]):
    print(f"Transaction {i+1}:")
    print(f"  Responsibility: {trans.get('responsibility', 'N/A')}")
    print(f"  Description: {trans.get('description', 'N/A')}")
    print(f"  Amount: {trans.get('amount', 'N/A')}")
    print(f"  Date: {trans.get('date', 'N/A')}")
    print(f"  Type: {trans.get('type', 'N/A')}")
    print("---")

print(f"\nTotal parsed: {len(transactions)}")