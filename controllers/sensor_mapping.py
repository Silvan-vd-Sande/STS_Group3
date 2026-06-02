DOT_TO_MAC_MAPPING = {'DOT-01': 'D4:22:CD:00:03:1E',
                      'DOT-02': 'D4:22:CD:00:03:20',
                      'DOT-03': 'D4:22:CD:00:03:1A',
                      'DOT-04': 'D4:22:CD:00:03:25',
                      'DOT-05': 'D4:22:CD:00:03:27',
                      'DOT-06': 'D4:22:CD:00:03:14',
                      'DOT-07': 'D4:22:CD:00:03:26',
                      'DOT-08': 'D4:22:CD:00:03:1C',
                      'DOT-09': 'D4:22:CD:00:03:15',
                      'DOT-10': 'D4:CA:6E:F0:BF:A5',
                      'DOT-11': 'D4:22:CD:00:63:78',
                      'DOT-12': 'D4:22:CD:00:63:89',
                      'DOT-13': 'D4:22:CD:00:63:7B',
                      'DOT-14': 'D4:22:CD:00:63:D2',
                      'DOT-15': 'D4:22:CD:00:63:88',
                      'DOT-16': 'D4:22:CD:00:63:D0',
                      'DOT-17': 'D4:22:CD:00:63:FE',
                      'DOT-18': 'D4:22:CD:00:63:D7',
                      'DOT-19': 'D4:22:CD:00:63:D5',
                      'DOT-20': 'D4:22:CD:00:64:7A',
                      'ROB-01': 'D4:22:CD:00:16:A1',
                      'ROB-02': 'D4:22:CD:00:16:9E',
                      'ROB-03': 'D4:22:CD:00:16:9D',
                      'ROB-04': 'D4:22:CD:00:16:A2',
                      'ROB-05': 'D4:22:CD:00:16:A4'
                      }

MAC_TO_DOT_MAPPING = {v: k for k, v in DOT_TO_MAC_MAPPING.items()}

def verify_dot_mapping(sensor_ids: list[str])-> bool:
    return all(sensor_id in DOT_TO_MAC_MAPPING.keys() for sensor_id in sensor_ids)
