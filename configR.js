{
"info":
    {
        "description": "this is a configration file",
        "date": "2019.08.15"
    },

"signal_processing":
    {
       "subject": "Test",
       "storage path": "f:\\data",
       "session": 1,
       "eeg channels": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16],
       "eeg channel label": ["AF1", "AF2", "C3", "C4"],
       "ref channels": [5,6],
       "ref channel label": ["T7", "T8"],
       "samplingrate": 128,
       "amplifier": "signal_generator",
       "amplifier params":{"remote device ip":"localhost","remote device port":51244},
       "sp_host_ip": "127.0.0.1",
       "sp_host_port": 9876,
       "sp_host_port1":9875,
       "result receiver address": [["127.0.0.1", 9877]]
    }
}
