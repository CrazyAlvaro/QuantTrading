# peg_single
# 05/09/18
# Yechen Huang

import jqdata
from jqfactor import Factor, calc_factors
import datetime
import numpy as np

def initialize(context):
    log.set_level('order', 'error')

    set_benchmark('000905.XSHG')

    # 开启动态复权
    set_option('use_real_price', True)

    # 将滑点设置为 系统默认值
    set_slippage(PriceRelatedSlippage(0.00246))

    # 调仓周期
    g.runner_counter = 0
    # run_weekly(market_open, 1, time='10:45', reference_security='000905.XSHG')
    run_monthly(market_open, 1, time='10:45', reference_security='000905.XSHG')

def market_open(context):
    """
    worker function being called from run_weekly/run_monthly
    """

    g.runner_counter += 1           # increase running counter

    set_cost_fee(context)

    # get all stock except 300 and 500 stocks
    universe = list(set(get_index_stocks('399001.XSHE') + get_index_stocks('000001.XSHG')) -
                    set(get_index_stocks('000300.XSHG') + get_index_stocks('000905.XSHG')))

    if g.runner_counter % 12 == 1:
    # if True:
        """
        factor_values = get_factor_values(context,
                                         [PE_RATIO(), PB_RATIO(), GROSS_MARGIN_AVERAGE(), \
                                         GROSS_MARGIN_GROWTH(), GROSS_MARGIN_STABILITY(), \
                                         GROSS_MARGIN()],
                                         universe)
        """

        factor_values = get_factor_values(context, [PEG_3YR_ADJ_PROFIT_PE_TTM()], universe)
        stock_list    = peg_stock_selection(factor_values)

        # 进行调仓
        rebalance_position(context, stock_list)

############################################
##  stock select model functions
############################################
def peg_stock_selection(factor_values):
    peg_ratio = factor_values['peg_3yr_adj_profit']
    peg_ratio.dropna(inplace=True)
    peg_ratio.sort(ascending=True)
    lowest_peg_stock = list(peg_ratio[21:40].index)

    return lowest_peg_stock

############################################
##  helper functions
############################################
def set_cost_fee(context):
    # 根据不同的时间段设置手续费
    dt=context.current_dt
    if dt>datetime.datetime(2013,1, 1):
        set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')

    elif dt>datetime.datetime(2011,1, 1):
        set_order_cost(OrderCost(close_tax=0.001, open_commission=0.001, close_commission=0.002, min_commission=5), type='stock')

    elif dt>datetime.datetime(2009,1, 1):
        set_order_cost(OrderCost(close_tax=0.001, open_commission=0.002, close_commission=0.003, min_commission=5), type='stock')

    else:
        set_order_cost(OrderCost(close_tax=0.001, open_commission=0.003, close_commission=0.004, min_commission=5), type='stock')

def bulk_orders(stock_list, target_value):
    """
    bulk order stock to target value
    """
    for stock in stock_list:
        order_target_value(stock, target_value)


def rebalance_position(context, stock_list):
    """
    rebalance portfolio according to current stock selection
    """
    current_holding = context.portfolio.positions.keys()

    # set_a - set_b: item in set_a but not in set_b
    buy_list  = list(set(stock_list) - set(current_holding))
    sell_list = list(set(current_holding) - set(stock_list))

    # sell stocks no longer in buy list
    bulk_orders(sell_list, 0)

    total_value = context.portfolio.available_cash

    # buy stocks that current on buy list
    if len(buy_list) > 0:
        bulk_orders(buy_list, total_value/len(buy_list))

def get_factor_values(context, factor_list, universe):
    """
    actually compute facctor list data
    """
    factor_name_list = list(factor.name for factor in factor_list)


    factor_values = calc_factors(universe,
                          factor_list,
                          context.previous_date,
                          context.previous_date)

    factor_dict = {factor:factor_values[factor].iloc[0] for factor in factor_name_list}
    return factor_dict

############################################
##  quality factors
############################################
class PEG_3YR_ADJ_PROFIT_PE_TTM(Factor):
    name = 'peg_3yr_adj_profit'
    yearly_trading_days = 246
    look_back_years = 3

    max_window =  yearly_trading_days * look_back_years + 1
    dependencies = ['pe_ratio_lyr', 'pe_ratio', 'adjusted_profit']

    def select_dataframe(self, df):
        # construct list
        index_list = []
        for i in range(self.look_back_years + 1):
            curr_index = self.yearly_trading_days * i
            if curr_index < len(df):
                index_list.append(curr_index)

        return df.iloc[index_list]

    def calc(self, data):
        adj_profit = self.select_dataframe(data['adjusted_profit'])
        pe_ratio= self.select_dataframe(data['pe_ratio'])

        look_back_lenth = len(adj_profit)

        early_adj_profit = adj_profit.iloc[0:look_back_lenth-1]
        later_adj_profit = adj_profit.iloc[1:look_back_lenth]

        growth_rate_df = later_adj_profit.div(early_adj_profit.values)
        growth_rate_prod = growth_rate_df.product(axis=0)
        growth_rate = growth_rate_prod ** (1/float(look_back_lenth)) - 1

        growth_rate      = growth_rate.to_frame().T
        growth_rate_prod = growth_rate_prod.to_frame().T

        # Get the latest pe ratio
        later_pe_ratio_lyr = pe_ratio.iloc[look_back_lenth-1:look_back_lenth]

        # peg = later_pe_ratio_lyr / (growth_rate*100)
        peg = later_pe_ratio_lyr.div(growth_rate.values*100)
        # peg_s = peg.iloc[0]

        growth_rate['new_index']      = later_pe_ratio_lyr.index.tolist()[0]
        growth_rate                   = growth_rate.set_index('new_index')
        growth_rate_prod['new_index'] = later_pe_ratio_lyr.index.tolist()[0]
        growth_rate_prod              = growth_rate_prod.set_index('new_index')

        # del growth_rate['new_index']
        peg = peg[later_pe_ratio_lyr>0]
        peg = peg[growth_rate_prod>0]
        peg = peg[growth_rate>0]
        peg.dropna(axis=1, how ='all', inplace=True)
        # peg.dropna(inplace=True)

        return peg.mean()


##################################################
# value factors
##################################################
class PB_RATIO(Factor):
    # 设置因子名称
    name = 'my_pb_ratio'
    # 设置获取数据的时间窗口长度
    max_window = 1
    # 设置依赖的数据
    dependencies = ['pb_ratio']
    # 计算因子的函数， 需要返回一个 pandas.Series, index 是股票代码，value 是因子值
    def calc(self, data):
        pb_ratio = data['pb_ratio']
        pb_ratio = pb_ratio[pd.notnull(pb_ratio)]
        return pb_ratio.mean()

class PE_TTM_RATIO(Factor):
    # 设置因子名称
    name = 'my_pe_ttm_ratio'
    # 设置获取数据的时间窗口长度
    max_window = 1
    # 设置依赖的数据
    dependencies = ['pe_ratio']
    # 计算因子的函数， 需要返回一个 pandas.Series, index 是股票代码，value 是因子值
    def calc(self, data):
        pe_ratio = data['pe_ratio']
        return pe_ratio.mean()

class PE_RATIO(Factor):
    # 设置因子名称
    name = 'my_pe_ratio'
    # 设置获取数据的时间窗口长度
    max_window = 1
    # 设置依赖的数据
    dependencies = ['pe_ratio_lyr']
    # 计算因子的函数， 需要返回一个 pandas.Series, index 是股票代码，value 是因子值
    def calc(self, data):
        pe_ratio = data['pe_ratio_lyr']
        return pe_ratio.mean()
