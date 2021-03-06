import numpy as np
from random import random, choice, choices


class Merchant:
    def __init__(self, **par):
        self.speculative_num = par['speculative_num']
        self.honest_num = par['honest_num']
        self.ID = par['ID']
        self.comment = par['comment']
        self.comment_bound = par['comment_bound']
        self.comment_count = par['comment_count']
        self.comment_system = par['comment_system']

        self.good_kind = par['good_kind']
        self.fake_rate = np.array(par['fake_rate'])
        self.fake_rate_lower_bound = par['fake_rate_lower_bound']
        self.fake_rate_upper_bound = par['fake_rate_upper_bound']

        self.fake_cost = par['fake_cost']
        self.fake_price = par['fake_price']
        self.real_cost = par['real_cost']
        self.real_price = par['real_price']

        self.decrease_fake_bound = par[
            'decrease_fake_bound']  # If the comment hit the bound, then the merchant will decrease the fake rate
        self.decrease_fake_rate = par['decrease_fake_rate']
        self.increase_fake_bound = par[
            'increase_fake_bound']  # When the bound is approached, the opportunistic merchant will increase the
        # fake rate.
        self.increase_fake_rate = par['increase_fake_rate']
        self.change_fake_rate = par['change_fake_rate']
        self.time_to_change = False

        self.sell_count = 0  # times the merchant sells goods.
        self.punished_count = 0  # how many times the merchant be punished
        self.money = 0

    def fake_change(self):
        if not self.change_fake_rate:
            return 0
        if self.comment < self.decrease_fake_bound and not self.time_to_change:
            self.time_to_change = True
        if not self.time_to_change:
            # i.e. not until first time reach decrease fake bound would the merchant change its fake rate.
            return 0
        if self.comment < self.decrease_fake_bound:
            self.fake_rate -= self.decrease_fake_rate
        elif self.comment > self.increase_fake_bound:
            self.fake_rate += self.increase_fake_rate
            self.fake_rate[self.fake_rate >= 1] = 1
        # self.fake_rate[np.logical_and( 0.001 < self.fake_rate, self.fake_rate <= fake_rate_lower_bound)] = fake_rate_lower_bound
        self.fake_rate[self.fake_rate >= self.fake_rate_upper_bound] = self.fake_rate_upper_bound
        self.fake_rate[self.fake_rate <= 0] = 0
        # if there no fake for sell when fake_sell=False, the fake rate of it is set to 0
        # self.fake_rate = [0 if fake_sell==False else rate for (rate,fake_sell) in zip(self.fake_rate,self.fake_sell)]

    def punished(self):
        pass
        # self.fake_rate[self.fake_rate >= 0] = 0
        # self.change_fake_rate=False

    def adjust_comment(self):
        if self.comment < 0:
            self.comment = 0
        if self.comment > self.comment_bound:
            self.comment = self.comment_bound


class Customer:
    def __init__(self, **par):
        self.num = par['num']
        self.ID = par['ID']
        self.buy_bound = par['buy_bound']
        self.prob_buy_good = par['prob_buy_good']  # the probability of buying each good in one round
        self.identify_fake_rate = par['identify_fake_rate']
        self.buy_bound_change_real = par['buy_bound_change_real']
        self.buy_bound_change_fake = par['buy_bound_change_fake']
        self.buy_comment_real = par['buy_comment_real']  # After buying something, the comment customer makes.
        self.buy_comment_fake = par['buy_comment_fake']
        self.prob_comment_on_real = par['prob_comment_on_real']
        self.prob_random_buy = par['prob_random_buy']  # Irrational customer.
        self.buy_with_weights = par['buy_with_weights']
        self.learning_fake_rate = par['learning_fake_rate']
        #  Parameter TBD

    def change_bound(self, perceive_real=None, buy_good_kind=None):
        """
        Change the buy_bound if bought something genuine or fake.
        Need some changes on the bound changing process, e.g., functional change?
        :param buy_good_kind:
        :param perceive_real:
        :return:
        """
        if perceive_real:
            self.buy_bound -= self.buy_bound_change_real[buy_good_kind]
        else:
            self.buy_bound += self.buy_bound_change_fake[buy_good_kind]
        if self.buy_bound < 0:
            self.buy_bound = 0
        elif self.buy_bound > 10:
            self.buy_bound = 10

    def random_buy(self):
        """
        Irrational in this round. Buy something randomly without considering his/her bound for goods.
        :return:
        """
        pass

    def increase_identify_rate(self, good_kind):
        self.identify_fake_rate[good_kind] += self.learning_fake_rate
        self.identify_fake_rate[self.identify_fake_rate > 1] = 1

    def buy(self, mers, mers_num):
        """
        Act.
        :param select_with_weights:
        :param good2buy:
        :param mers: from _mers to choose someone to buy
        :param mers_num:
        :return:
        """
        index, mers = bound_choose(mers, mers_num, self.buy_bound)  # buying with consideration of the bound.
        index = random_choose(index, mers_num, self.prob_random_buy)  # irrational: randomly choose someone to buy.
        if index == 0:  # No merchant to buy.
            return -1, None, None, None
        if self.buy_with_weights:
            # to ensure that comment 0 still could be bought.
            weights = [_.comment + self.prob_random_buy for _ in mers[:index]]
            merchant2buy = choices(mers[:index], weights)[0]
        else:
            merchant2buy = choice(mers[:index])
        good_kind = choices(merchant2buy.good_kind, self.prob_buy_good)[0]  # type of good to be bought
        fake_rate = merchant2buy.fake_rate[good_kind]
        identify_fake_rate = self.identify_fake_rate[good_kind]  # rate for identifying such good
        rand = random()
        perceive_type = True  # Customer's thought
        true_type = True  # Goods real type

        if rand < fake_rate:  # selling fake
            found_fake = True
            # found by the customer
            if choices([found_fake, False], [identify_fake_rate, 1 - identify_fake_rate])[0]:
                self.change_bound(False, good_kind)
                self.increase_identify_rate(good_kind)
                true_type = False
                perceive_type = False
            # Merchant sold fake but wasn't found by the customer.
            else:
                self.change_bound(True, good_kind)
                true_type = False
                perceive_type = True
        else:
            # selling real
            # Default
            self.change_bound(True, good_kind)

        merchant2buy.money += revenue(true_type, good_kind, merchant2buy)
        merchant2buy.sell_count += 1
        return perceive_type, merchant2buy.ID, good_kind, true_type


class Regulator:
    def __init__(self, **par):
        """

        :param par:
        """
        self.num = par['num']
        self.ID = par['ID']
        self.lazy_identify_rate = par['lazy_identify_rate']  # Lazily regulate.
        self.lazy_cost_rate = par['lazy_cost_rate']
        self.diligent_identify_rate = par[
            'diligent_identify_rate']  # The ability to spot the fake when diligently regulate the market.
        self.diligent_cost_rate = par['diligent_cost_rate']
        self.punishment_money_multiple = par['punishment_money_multiple']
        self.punishment_comment = par['punishment_comment']
        self.fine_got = 0
        self.check_cost = 0
        self.whether_check_market = par['whether_check_market']
        self.check_with_weights = par['check_with_weights']
        self.prob_random_check = par['prob_random_check']
        self.lazy = par['lazy']
        self.prob_check_good = par['prob_check_good']
        self.check_inside_market = par['check_inside_market']
        # self.make_public = True

    def check_market(self, mers=None):
        """
        To check the market.
        :return:
        """
        if not self.whether_check_market:
            return 0
        if self.check_with_weights:
            # 0.1 is set to ensure that merchants with comment 10 still have a chance to be checked.
            weight = mers[0].comment_bound - np.array([mer.comment for mer in mers])
            merchant2check = choices(mers, weight)[0]
        else:
            merchant2check = choice(mers)
        good2check = choices(merchant2check.good_kind, self.prob_check_good)[0]
        fake_rate = merchant2check.fake_rate[good2check]
        fake_price = merchant2check.fake_price[good2check]
        real_price = merchant2check.real_price[good2check]
        rand_false = random()
        true_type = True
        punished_mark = False
        lazy = False
        if rand_false <= fake_rate:  # the merchant sells fake good
            rand_identify = random()
            true_type = False
            if self.lazy:  # the regulator is lazy
                lazy = True
                if self.lazy_identify_rate >= rand_identify:
                    # Merchant sold fake good and was caught.
                    self.punish(fake_price, lazy=True, mer=merchant2check)
                    punished_mark = True
            else:  # the regulator is diligent
                if self.diligent_identify_rate >= rand_identify:
                    self.punish(fake_price, lazy=False, mer=merchant2check)
                    punished_mark = True
            self.check_cost += fake_price * (self.lazy_cost_rate if lazy else self.diligent_cost_rate)
        self.check_cost += real_price * (self.lazy_cost_rate if lazy else self.diligent_cost_rate)
        if self.check_inside_market:
            if not punished_mark:
                merchant2check.money += revenue(true_type, good2check, merchant2check)
            else:
                merchant2check.money -= merchant2check.fake_cost[good2check]
        else:
            pass

    def punish(self, good_price=None, lazy=None, mer=None):
        mer.punished_count += 1
        punishment_money = self.punishment_money_multiple * good_price
        mer.money -= punishment_money
        if mer.comment_system:
            mer.comment -= self.punishment_comment
        mer.comment = .0 if mer.comment < .0 else mer.comment
        mer.punished()
        self.fine_got += punishment_money

    def make_public(self):
        pass


def random_choose(index, mers_num, p_random):
    """
    if random()>p_random, i.e., not randomly choose who to buy.
    :param index: chose by bound_choose
    :param mers_num: overall mers' number
    :param p_random: prob one randomly buy something
    :return:
    """
    if random() > p_random:
        return index
    else:
        return mers_num


def bound_choose(mers, mers_num, bound):
    _mer = sorted(mers, key=lambda x: x.comment, reverse=True)
    _iter = filter(lambda x: x.comment < bound, _mer)
    try:
        index = _mer.index(next(_iter))
    except StopIteration:
        index = mers_num
    return index, _mer


def revenue(real=None, good_kind=None, merchant2buy=None):
    if not real:
        price = merchant2buy.fake_price[good_kind]
        cost = merchant2buy.fake_cost[good_kind]
    else:
        price = merchant2buy.real_price[good_kind]
        cost = merchant2buy.real_cost[good_kind]
    return price - cost
