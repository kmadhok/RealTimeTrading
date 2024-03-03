from configparser import ConfigParser
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import OrderRequest
from alpaca.trading.enums import OrderSide, OrderType, OrderClass, TimeInForce
import csv

# Assume these are your API credentials (you should secure them, not hard-code them!)
api_key = 'PKBSMA05S2WDBRDKZVDX'
secret_key = 'SUcB01ge2dycnArTOJNPdAtimmcUKgU4txCeKbJ1'

# Initialize the TradingClient
trading_client = TradingClient(
    api_key=api_key,
    secret_key=secret_key,
    paper=True
)

def perform_trade(data):
    """
    Perform a trade based on the given data.

    Parameters:
    data (dict): A dictionary containing the trade information, 
                 should include 'symbol', 'qty', 'side', 'type', and 'order_class'.
    """
    # Create the order request based on the data provided
    order_request = OrderRequest(
        symbol=data['symbol'],
        qty=float(data['qty']),
        side=OrderSide[data['side']],
        type=OrderType[data['type']],
        order_class=OrderClass[data['order_class']],
        time_in_force='ioc',  # You can make this dynamic as well based on your data structure
        extended_hours=False  # Same here, adjust as needed
    )

    # Submit the order
    order_submission_response = trading_client.submit_order(order_data=order_request)
    print(order_submission_response)
    return order_submission_response  # Return the response for further processing if needed

# Example usage, replace with your actual streaming data handling
if __name__ == '__main__':
    # Read orders from a CSV file and submit them - you might replace this with streamed data handling
    csv_file_path='/Users/kanumadhok/Desktop/Desktop Kanu/UChicago/Class/Real TIme/Final_Project/NewExample/random_signals.csv'
    with open(csv_file_path, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            perform_trade(row)  # Here we pass the row dict directly to perform_trade
