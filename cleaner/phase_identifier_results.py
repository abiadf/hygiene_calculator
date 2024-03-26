'''Make object of phase identifying class'''

# import phase_identifier as pi

# post_milk_flush_time, post_milk_flush_idx= pi.PhaseIdentifier.find_post_milk_time()
# prerinse_time, prerinse_idx              = pi.PhaseIdentifier.find_prerinse_time(post_milk_flush_time, post_milk_flush_idx, neighbors_interval = 10)
# low_C_zone_KPIs                         = pi.PhaseIdentifier.get_low_C_zone_KPIs(post_milk_flush_time, post_milk_flush_idx)
# hot_rinse_time, hot_rinse_idx            = pi.PhaseIdentifier.find_hot_rinse_time(low_C_zone_KPIs, prerinse_time, prerinse_idx, neighbors_interval = 8)
# post_rinse_time, post_rinse_idx          = pi.PhaseIdentifier.find_post_rinse_time(hot_rinse_time, neighbors_interval = 20)
# rinse_KPIs                            = pi.PhaseIdentifier.collect_rinse_KPIs(hot_rinse_idx, post_rinse_idx, low_C_zone_KPIs)


# class ResultingPhases():

#     def __init__(self, solution_type):
#         self.post_milk_flush_time, self.post_milk_flush_idx= pi.PhaseIdentifier.find_post_milk_time()
#         self.prerinse_time, self.prerinse_idx              = pi.PhaseIdentifier.find_prerinse_time(self.post_milk_flush_time, self.post_milk_flush_idx, neighbors_interval = 10)
#         self.low_C_zone_KPIs                              = pi.PhaseIdentifier.get_low_C_zone_KPIs(self.post_milk_flush_time, self.post_milk_flush_idx)
#         self.hot_rinse_time, self.hot_rinse_idx            = pi.PhaseIdentifier.find_hot_rinse_time(self.low_C_zone_KPIs, self.prerinse_time, self.prerinse_idx, neighbors_interval = 8)
#         self.post_rinse_time, self.post_rinse_idx          = pi.PhaseIdentifier.find_post_rinse_time(self.hot_rinse_time, neighbors_interval = 20)
#         self.rinse_KPIs                                 = pi.PhaseIdentifier.collect_rinse_KPIs(self.hot_rinse_idx, self.post_rinse_idx, self.low_C_zone_KPIs, solution_type)
