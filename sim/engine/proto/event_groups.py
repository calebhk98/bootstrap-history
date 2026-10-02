"""One historical disaster is one event, its consequences listed inside it."""

# Fewest consequences worth folding into a single event.
MIN_GROUPED_CONSEQUENCES = 2


def group_disaster_events(events, disaster_name, disaster_messages):
    """`events` with the run of lines the disaster produced replaced by one event.

    The grouped event carries the whole list under `details`, so nothing is lost."""
    if not disaster_name or len(disaster_messages) < MIN_GROUPED_CONSEQUENCES:
        return events
    wanted = list(disaster_messages)
    start = next((index for index in range(len(events) - len(wanted) + 1)
                  if [event["message"] for event in events[index:index + len(wanted)]] == wanted), None)
    if start is None:
        return events
    members = events[start:start + len(wanted)]
    grouped = {"year": members[0]["year"],
               "message": "%s: %d consequences" % (disaster_name, len(members)),
               "details": [member["message"] for member in members]}
    return events[:start] + [grouped] + events[start + len(wanted):]
