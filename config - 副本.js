{
"info":
    {
        "description": "this is a configration file",
        "date": "2019.08.15"
    },

"signal_processing":
    {
       "subject": "Test",
       "save data": true,
       "storage path": "f:\\data",
       "session": 1,
       "eeg channels": [1, 2, 3, 4],
       "eeg channel label": ["AF1", "AF2", "C3", "C4"],
       "ref channels": [5,6],
       "ref channel label": ["T7", "T8"],
       "samplingrate": 100,
       "amplifier": "signal_generator",
       "amplifier params":{},
       "sp_host_ip": "127.0.0.1",
       "sp_host_port": 9876,
       "sp_host_port1":9875,
       "result receiver address": [["127.0.0.1", 9877]]
    }
}
