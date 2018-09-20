from pm4py.models.petri import visualize
from pm4py.algo.discovery.dfg import factory as dfg_factory
from pm4py.models.petri import vis_trans_shortest_paths
from pm4py.filtering.tracelog.attributes import attributes_filter

def get_decorated_net(net, initial_marking, final_marking, log, parameters=None, variant="frequency"):
    """
    Get a decorated net according to the specified variant (decorate Petri net based on DFG)

    Parameters
    ------------
    net
        Petri net
    initial_marking
        Initial marking
    final_marking
        Final marking
    parameters
        Algorithm parameters
    variant
        Specify if the decoration should take into account the frequency or the performance

    Returns
    ------------
    gviz
        GraphViz object
    """
    if parameters is None:
        parameters = {}

    if "frequency" in variant:
        aggregationMeasure = "sum"
    elif "performance" in variant:
        aggregationMeasure = "performance"

    if "aggregationMeasure" in parameters:
        aggregationMeasure = parameters["aggregationMeasure"]

    # we find the DFG
    dfg = dfg_factory.apply(log, variant=variant, parameters=parameters)
    # we find shortest paths
    spaths = vis_trans_shortest_paths.get_shortest_paths(net)
    # we find the number of activities occurrences in the trace log
    activities_count = attributes_filter.get_activities_from_log(log, parameters=parameters)
    aggregated_statistics = vis_trans_shortest_paths.get_net_decorations_from_dfg_spaths_acticount(net, dfg, spaths,
                                                                                                   activities_count,
                                                                                                   variant=variant,
                                                                                                   aggregationMeasure=aggregationMeasure)
    return visualize.apply(net, initial_marking, final_marking, parameters=parameters,
                           decorations=aggregated_statistics)

def apply_frequency(net, initial_marking, final_marking, log=None, aggregated_statistics=None, parameters=None):
    """
    Apply frequency decoration through greedy algorithm (decorate Petri net based on DFG)

    Parameters
    ------------
    net
        Petri net
    initial_marking
        Initial marking
    final_marking
        Final marking
    parameters
        Algorithm parameters

    Returns
    ------------
    gviz
        GraphViz object
    """
    return get_decorated_net(net, initial_marking, final_marking, log, parameters=parameters, variant="frequency")

def apply_performance(net, initial_marking, final_marking, log=None, aggregated_statistics=None, parameters=None):
    """
    Apply performance decoration through greedy algorithm (decorate Petri net based on DFG)

    Parameters
    ------------
    net
        Petri net
    initial_marking
        Initial marking
    final_marking
        Final marking
    parameters
        Algorithm parameters

    Returns
    ------------
    gviz
        GraphViz object
    """
    return get_decorated_net(net, initial_marking, final_marking, log, parameters=parameters, variant="performance")