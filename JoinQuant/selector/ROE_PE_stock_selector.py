from datetime import timedelta, date
import pandas as pd

# These are JoinQuant functions and structures
from JoinQuant import get_price, get_security_info, get_fundamentals, query
from JoinQuant import income, valuation, indicator

# 一些功能函数
def get_tick_price(stock):
#     return get_ticks(stock, end_dt=date.today().strftime("%Y-%m-%d"), count=1)[0][1]
    return get_price(stock, count = 1, end_date=date.today().strftime("%Y-%m-%d"), \
                    frequency='daily', fields=['close']).iloc[0,0]

def add_name(stock_list):
    stock_list["name"] = None
    stock_list["price"] = None
    stock_list["pe"] = None
    cols = stock_list.columns.tolist()
    cols = cols[-1:] + cols[:-1]
    stock_list = stock_list[cols]

    for stock in stock_list.index:
        stock_list.loc[stock, "name"] = get_security_info(stock).display_name
        stock_list.loc[stock, "price"] = get_tick_price(stock)
        if not stock_list.loc[stock, "eps"] == 0:
            stock_list.loc[stock, "pe"] = stock_list.loc[stock, "price"] / stock_list.loc[stock, "eps"]
        else:
            stock_list.loc[stock, "pe"] = np.inf

    return stock_list

def get_financial_stats(date):
    return get_fundamentals(
                query(income.code,
                      indicator.inc_revenue_year_on_year,
                  valuation.pe_ratio_lyr,
                  valuation.pe_ratio,
                  indicator.adjusted_profit,
                  indicator.inc_net_profit_year_on_year,
                  indicator.adjusted_profit_to_profit,
                  indicator.roe,
                  indicator.roa,
                  indicator.eps),
                statDate = date)


########################################
# get some data and do some filtering
########################################
df_23Q3 = get_financial_stats('2023Q3')
df_23Q2 = get_financial_stats('2023Q2')
df_23Q1 = get_financial_stats('2023Q1')
df_22 = get_financial_stats('2022')
df_23Q1.set_index('code', inplace=True)
df_23Q2.set_index('code', inplace=True)
df_23Q3.set_index('code', inplace=True)
df_22.set_index('code', inplace=True)


########################################
# sum and sort
########################################
df_23Q3["roe"] = df_23Q3["roe"] + df_23Q2["roe"] + df_23Q1["roe"]
df_23Q3["eps"] = df_23Q3["eps"] + df_23Q2["eps"] + df_23Q1["eps"]
df_23Q3[:10]


df=df_23Q3.copy()
slt_df = df[(df["adj_prft_mrgn"]>60) &
            (df["eps"]>0) &
            (df["roe"]>10) &
            (df["pe"]<25) &
            (df["profit_growth_yoy"]>15) &
            (df["revenue_growth_yoy"]>15) &
            (df["adjusted_profit"]>0)]
# print(slt_df.shape)
sort_df = slt_df.sort_values(by=["pe"])
sort_df[:30]