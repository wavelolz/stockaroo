import numpy as np

def FilterMonths(year, min_date, max_date):
    months = list(range(1, 13))
    if year == min_date.year and year == max_date.year:
        return list(range(min_date.month, max_date.month + 1))
    elif year == min_date.year:
        return list(range(min_date.month, 13))
    elif year == max_date.year:
        return list(range(1, max_date.month + 1))
    else:
        return months

def FilterQuarters(year, min_date, max_date):
    quarter_month_map = {
    "Q1": (1, 3),
    "Q2": (4, 6),
    "Q3": (7, 9),
    "Q4": (10, 12)
    }
    valid_quarters = []
    for quarter, (start_month, end_month) in quarter_month_map.items():
        if ((year == min_date.year and end_month >= min_date.month) or year > min_date.year) and \
           ((year == max_date.year and start_month <= max_date.month) or year < max_date.year):
            valid_quarters.append(quarter)
    return valid_quarters

def CalculateInvestmentReturns(filtered_data, duration_type, MIA=1000):
    if not filtered_data.empty:
        if duration_type == "Month":
            group_cols = ['year', 'month']
        elif duration_type == "Quarter":
            group_cols = ['year', 'quarter']
        elif duration_type == "Year":
            group_cols = ['year']
        
        first_days = filtered_data.groupby(group_cols).first().reset_index(drop=True)
        last_days = filtered_data.groupby(group_cols).last().reset_index(drop=True)
        
        # Initialize variables to store results
        durations = np.arange(len(first_days)) + 1  # Durations from 0 to the number of periods - 1

        # Calculate cumulative stock bought for each period
        opening_prices = first_days['open'].values
        closing_prices = last_days['close'].values

        cumulative_stock = np.cumsum(MIA / opening_prices)
        cost = np.cumsum([MIA] * len(opening_prices))
        revenue = np.round(cumulative_stock * closing_prices, 2)

        # Calculate the invested amount for each period
        invested_amounts = MIA * (durations)

        # Calculate profit ratios
        ROI = np.round((revenue - invested_amounts) / invested_amounts * 100, 2)
        
        # Return the results as a list of lists
        return [durations.tolist(), cost.tolist(), revenue.tolist(), ROI.tolist()]
    else:
        return [[], [], [], []]  # Return empty lists if filtered_data is empty