import time
from gnuradio import uhd

def wait_for_pps_edge(usrp_block, poll_s=0.0001):
    last = usrp_block.get_time_last_pps().get_real_secs()
    while True:
        time.sleep(poll_s)
        cur = usrp_block.get_time_last_pps().get_real_secs()
        if cur != last:
            return cur

def arm_time_reset_next_pps(usrp_block):
    wait_for_pps_edge(usrp_block)
    usrp_block.set_time_next_pps(uhd.time_spec(0.0))
    wait_for_pps_edge(usrp_block)
