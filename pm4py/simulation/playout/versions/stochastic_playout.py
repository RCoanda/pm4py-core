import datetime
from copy import copy
from random import choice

import pm4py.objects.log.log as log_instance
from pm4py.objects.petri import semantics
from pm4py.util import exec_utils
from pm4py.util import xes_constants
from enum import Enum
from pm4py.util import constants
from pm4py.simulation.montecarlo.utils import replay
from pm4py.objects.petri.common import final_marking as final_marking_discovery
from pm4py.objects.stochastic_petri import utils as stochastic_utils


class Parameters(Enum):
    ACTIVITY_KEY = constants.PARAMETER_CONSTANT_ACTIVITY_KEY
    TIMESTAMP_KEY = constants.PARAMETER_CONSTANT_TIMESTAMP_KEY
    CASE_ID_KEY = constants.PARAMETER_CONSTANT_CASEID_KEY
    NO_TRACES = "noTraces"
    MAX_TRACE_LENGTH = "maxTraceLength"
    LOG = "log"
    STOCHASTIC_MAP = "stochastic_map"


def apply_playout(net, initial_marking, no_traces=100, max_trace_length=100,
                  case_id_key=xes_constants.DEFAULT_TRACEID_KEY,
                  activity_key=xes_constants.DEFAULT_NAME_KEY, timestamp_key=xes_constants.DEFAULT_TIMESTAMP_KEY,
                  final_marking=None, smap=None, log=None):
    """
    Do the playout of a Petrinet generating a log

    Parameters
    ----------
    net
        Petri net to play-out
    initial_marking
        Initial marking of the Petri net
    no_traces
        Number of traces to generate
    max_trace_length
        Maximum number of events per trace (do break)
    case_id_key
        Trace attribute that is the case ID
    activity_key
        Event attribute that corresponds to the activity
    timestamp_key
        Event attribute that corresponds to the timestamp
    final_marking
        If provided, the final marking of the Petri net
    smap
        Stochastic map
    log
        Log
    """
    if final_marking is None:
        # infer the final marking from the net
        final_marking = final_marking_discovery.discover_final_marking(net)
    if smap is None:
        if log is None:
            raise Exception("please provide at least one between stochastic map and log")
        smap = replay.get_map_from_log_and_net(log, net, initial_marking, final_marking)
    # assigns to each event an increased timestamp from 1970
    curr_timestamp = 10000000
    log = log_instance.EventLog()
    for i in range(no_traces):
        trace = log_instance.Trace()
        trace.attributes[case_id_key] = str(i)
        marking = copy(initial_marking)
        while len(trace) < max_trace_length:
            if not semantics.enabled_transitions(net, marking):  # supports nets with possible deadlocks
                break
            all_enabled_trans = semantics.enabled_transitions(net, marking)
            if final_marking is not None and marking == final_marking:
                en_t_list = list(all_enabled_trans.union({None}))
            else:
                en_t_list = list(all_enabled_trans)

            trans = stochastic_utils.pick_transition(en_t_list, smap)

            if trans is None:
                break
            if trans.label is not None:
                event = log_instance.Event()
                event[activity_key] = trans.label
                event[timestamp_key] = datetime.datetime.fromtimestamp(curr_timestamp)
                trace.append(event)
                # increases by 1 second
                curr_timestamp += 1
            marking = semantics.execute(trans, net, marking)
        log.append(trace)
    return log


def apply(net, initial_marking, final_marking=None, parameters=None):
    """
    Do the playout of a Petrinet generating a log

    Parameters
    -----------
    net
        Petri net to play-out
    initial_marking
        Initial marking of the Petri net
    final_marking
        If provided, the final marking of the Petri net
    parameters
        Parameters of the algorithm:
            Parameters.NO_TRACES -> Number of traces of the log to generate
            Parameters.MAX_TRACE_LENGTH -> Maximum trace length
    """
    if parameters is None:
        parameters = {}
    case_id_key = exec_utils.get_param_value(Parameters.CASE_ID_KEY, parameters, xes_constants.DEFAULT_TRACEID_KEY)
    activity_key = exec_utils.get_param_value(Parameters.ACTIVITY_KEY, parameters, xes_constants.DEFAULT_NAME_KEY)
    timestamp_key = exec_utils.get_param_value(Parameters.TIMESTAMP_KEY, parameters,
                                               xes_constants.DEFAULT_TIMESTAMP_KEY)
    no_traces = exec_utils.get_param_value(Parameters.NO_TRACES, parameters, 1000)
    max_trace_length = exec_utils.get_param_value(Parameters.MAX_TRACE_LENGTH, parameters, 1000)
    smap = exec_utils.get_param_value(Parameters.STOCHASTIC_MAP, parameters, None)
    log = exec_utils.get_param_value(Parameters.LOG, parameters, None)

    return apply_playout(net, initial_marking, max_trace_length=max_trace_length, no_traces=no_traces,
                         case_id_key=case_id_key, activity_key=activity_key, timestamp_key=timestamp_key,
                         final_marking=final_marking, smap=smap, log=log)
