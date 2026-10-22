"""START pause-menu strings verified against A4NE rev 0 and b8471ae.

Diary: asm/new_game.s 08003BC0..080048A0; native statistics/bag:
asm/code_0803EE94.s; map: descriptor table 080FD080..080FD3A0,
20-byte records, two text pointers followed by unchanged map coordinates.
Every source payload and pointer is checked before insertion.
"""
from fomt_text import FormatError, ROM_BASE, cstring, make_record, u32

# ID, offset, literal/table pointer slots, exact source bytes, cells, group, byte limit.
SPECS = (
    ('ui.start.0e86a8', 951976, (952068,), '4469617279', 12, 'diary', None),
    ('ui.start.0e86b0', 951984, (952072,), '53617665', 8, 'diary', None),
    ('ui.start.0e86b8', 951992, (952076,), '4c6f6164', 6, 'diary', None),
    ('ui.start.0e86c4', 952004, (952084,), '446174612031', 8, 'diary', None),
    ('ui.start.0e86cc', 952012, (952088,), '446174612032', 6, 'diary', None),
    ('ui.start.0e86d4', 952020, (952092,), '427574746f6e73', 12, 'diary', None),
    ('ui.start.0e86e4', 952036, (952104,), '436c6f636b', 12, 'diary', None),
    ('ui.start.0e86ec', 952044, (18488, 18584, 952108, 952120, 952132), '596573', 6, 'diary', None),
    ('ui.start.0e86f0', 952048, (18492, 18588, 952112, 952124, 952136), '4e6f', 6, 'diary', None),
    ('ui.start.0e86f4', 952052, (952116,), '46616365', 12, 'diary', None),
    ('ui.start.0e86fc', 952060, (952128,), '4e616d65', 12, 'diary', None),
    ('ui.start.0e874c', 952140, (15140,), '5965617273', 28, 'diary', None),
    ('ui.start.0e8758', 952152, (15148,), '20446179', 28, 'diary', None),
    ('ui.start.0e8768', 952168, (15160,), '204661726d', 28, 'diary', None),
    ('ui.start.0e8770', 952176, (16180,), '526561642064696172792e', 28, 'diary', None),
    ('ui.start.0e877c', 952188, (16176,), '577269746520696e2064696172792e', 28, 'diary', None),
    ('ui.start.0e878c', 952204, (16224, 18528), '5468657265206973206e6f20736176656420646174612e', 28, 'diary', None),
    ('ui.start.0e87a4', 952228, (16232,), '436f6e74726f6c7320202020202020203120202020202020320d0a436f6e74726f6c20506164202020202057616c6b2020202052756e0d0a5220427574746f6e202020202020202052756e202020202057616c6b', 28, 'diary', None),
    ('ui.start.0e87fc', 952316, (16240,), '53686f77206f7220686964652074686520436c6f636b200d0a696e20746865204d61702057696e646f77', 28, 'diary', None),
    ('ui.start.0e8828', 952360, (16248,), '53686f77206f722068696465207468652066616365206f66200d0a74686520706572736f6e20796f752772652074616c6b696e670d0a746f20696e20746865204d6573736167652057696e646f7705', 28, 'diary', None),
    ('ui.start.0e8878', 952440, (16276,), '53686f77206f72206869646520746865206e616d65206f66200d0a74686520706572736f6e20796f752772652074616c6b696e670d0a746f20696e20746865204d6573736167652057696e646f7705', 28, 'diary', None),
    ('ui.start.0e88c8', 952520, (16540,), '53617665206661696c65642e05', 28, 'diary', None),
    ('ui.start.0e88d8', 952536, (16856,), '4c6f6164206661696c65642e0d0a5468652073617665642064617461206d61790d0a626520636f727275707465642e05', 28, 'diary', None),
    ('ui.start.0e890c', 952588, (18484,), '4c6f61643f', 28, 'diary', 28),
    ('ui.start.0e8914', 952596, (18580,), '4f76657277726974653f', 28, 'diary', 28),
    ('ui.start.0f05b8', 984504, (888204, 891300), '43726f7073', 12, 'tutorial', 12),
    ('ui.start.0f05c0', 984512, (888208, 891304), '416e696d616c73', 12, 'tutorial', 12),
    ('ui.start.0f05c8', 984520, (888212, 891308), '55736566756c2054697073', 12, 'tutorial', 12),
    ('ui.start.0f05d4', 984532, (888216, 891312), '45786974', 12, 'tutorial', 12),
    ('ui.start.0fb824', 1030180, (393384,), '2050726f706572747920', 10, 'statistics', None),
    ('ui.start.0fb838', 1030200, (405424,), '4865616c74687920', 8, 'statistics', None),
    ('ui.start.0fb844', 1030212, (405820,), '556e686170707920', 8, 'statistics', None),
    ('ui.start.0fb850', 1030224, (406124,), '5369636b20202020', 8, 'statistics', None),
    ('ui.start.0fb85c', 1030236, (406408, 420620), '537072696e67', 6, 'statistics', None),
    ('ui.start.0fb864', 1030244, (406692, 420904), '53756d6d6572', 6, 'statistics', None),
    ('ui.start.0fb86c', 1030252, (406976, 421192), '46616c6c2020', 6, 'statistics', None),
    ('ui.start.0fb874', 1030260, (407260, 421480), '57696e746572', 6, 'statistics', None),
    ('ui.start.0fb87c', 1030268, (407540,), '7972', 3, 'statistics', None),
    ('ui.start.0fb880', 1030272, (410500,), '4c697374206f6620436869636b656e73', 16, 'statistics', None),
    ('ui.start.0fb894', 1030292, (410712,), '4c697374206f6620436174746c65', 16, 'statistics', None),
    ('ui.start.0fb8a4', 1030308, (410984,), '4c697374206f6620536865657020', 16, 'statistics', None),
    ('ui.start.0fb8b4', 1030324, (411324,), '48617276657374205370726974657320', 16, 'statistics', None),
    ('ui.start.0fb8cc', 1030348, (411684,), '6c656674', 4, 'statistics', None),
    ('ui.start.0fb8d4', 1030356, (411976,), '776f726b20202020', 8, 'statistics', None),
    ('ui.start.0fb8e0', 1030368, (412268,), '4e2f41202020202020202020', 12, 'statistics', None),
    ('ui.start.0fb8f0', 1030384, (419192,), '4561726e696e6773205265706f727420', 16, 'statistics', None),
    ('ui.start.0fb90c', 1030412, (421788,), '59656172', 4, 'statistics', None),
    ('ui.start.0fb914', 1030420, (422104,), '496e636f6d65', 6, 'statistics', None),
    ('ui.start.0fb91c', 1030428, (422416,), '457870656e736573', 8, 'statistics', None),
    ('ui.start.0fb928', 1030440, (427004,), '546f6f6c204c6576656c204c69737420', 16, 'statistics', None),
    ('ui.start.0fb93c', 1030460, (427024,), '53686f702020', 6, 'statistics', None),
    ('ui.start.0fb944', 1030468, (427368,), '557067726164653f', 8, 'statistics', None),
    ('ui.start.0fbe7c', 1031804, (462440,), '4e756d6265722073686970706564', 22, 'statistics', None),
    ('ui.start.0fbe90', 1031824, (464016,), '46697368696e6720', 8, 'statistics', None),
    ('ui.start.0fbe9c', 1031836, (464028,), '4e616d65', 4, 'statistics', None),
    ('ui.start.0fbea4', 1031844, (464448,), '4d6178696d756d2073697a65', 12, 'statistics', None),
    ('ui.start.0fbeb4', 1031860, (464748,), '526573756c747320', 8, 'statistics', None),
    ('ui.start.0fbec0', 1031872, (465048,), '66697368', 4, 'statistics', None),
    ('ui.start.0fbed8', 1031896, (468156,), '4f7468657220', 6, 'statistics', None),
    ('ui.start.0fbefc', 1031932, (469004,), '4861727665737420', 9, 'statistics', None),
    ('ui.start.0fbf08', 1031944, (469300,), '416e696d616c2048757362616e647279', 16, 'statistics', None),
    ('ui.start.0fbf1c', 1031964, (469596,), '5761746572696e67', 8, 'statistics', None),
    ('ui.start.0fbf28', 1031976, (469892,), '4672697362656520', 8, 'statistics', None),
    ('ui.start.0fbf34', 1031988, (471068,), '7365632e', 4, 'statistics', None),
    ('ui.start.0fbf58', 1032024, (472384,), '4869676865737420616d6f756e74', 14, 'statistics', None),
    ('ui.start.0fbf68', 1032040, (472688,), '6561726e65642020', 8, 'statistics', None),
    ('ui.start.0fbf74', 1032052, (472992,), '7573656420202020', 8, 'statistics', None),
    ('ui.start.0fbfa0', 1032096, (474576,), '436869636b656e20', 8, 'statistics', None),
    ('ui.start.0fbfac', 1032108, (474880,), '436f7720', 4, 'statistics', None),
    ('ui.start.0fbfb4', 1032116, (475184,), '536865657020', 6, 'statistics', None),
    ('ui.start.0fbfbc', 1032124, (475488,), '796561727320', 6, 'statistics', None),
    ('ui.start.0fbff0', 1032176, (478604,), '6c6576656c732062656c6f772067726f756e6420', 20, 'statistics', None),
    ('ui.start.0fc008', 1032200, (479028,), '4e756d626572206f66206d6f6c657320776861636b656420', 24, 'statistics', None),
    ('ui.start.1000b4', 1048756, (574192,), '546f6f6c73', 8, 'rucksack', 11),
    ('ui.start.1000bc', 1048764, (574196,), '4974656d73', 8, 'rucksack', 11),
    ('ui.start.0fc6f0', 1033968, (1036416, 1036420), '4d6f756e7461696e20436f7474616765', 28, 'world_map', None),
    ('ui.start.0fc704', 1033988, (1036436, 1036440), '5365617369646520436f7474616765', 28, 'world_map', None),
    ('ui.start.0fc714', 1034004, (1036456, 1036460), '546f776e20436f7474616765', 28, 'world_map', None),
    ('ui.start.0fc724', 1034020, (1036476, 1036480), '54696d652057696e646f770d0a54686973206973207468652070726573656e7420736561736f6e2e', 28, 'world_map', None),
    ('ui.start.0fc750', 1034064, (1036496, 1036500), '54696d652057696e646f770d0a5468697320697320746f646179277320646174652e', 28, 'world_map', None),
    ('ui.start.0fc774', 1034100, (1036516, 1036520), '54696d652057696e646f770d0a5468697320697320746f6461792773206461792e', 28, 'world_map', None),
    ('ui.start.0fc798', 1034136, (1036536, 1036540), '54696d652057696e646f770d0a54686973206973207468652063757272656e742074696d652e', 28, 'world_map', None),
    ('ui.start.0fc7c0', 1034176, (1036556, 1036560), '54696d652057696e646f770d0a5468697320697320746f646179277320776561746865722e', 28, 'world_map', None),
    ('ui.start.0fc7e8', 1034216, (1036576, 1036580), '54696d652057696e646f77', 28, 'world_map', None),
    ('ui.start.0fc7f4', 1034228, (1036596, 1036600), '426173696c277320486f757365', 28, 'world_map', None),
    ('ui.start.0fc804', 1034244, (1036616,), '4d6172792773204c696272617279200d0a546865726520617265206d616e7920626f6f6b732e', 28, 'world_map', None),
    ('ui.start.0fc82c', 1034284, (1036620,), '4d6172792773204c6962726172790d0a486f7572733a203130414d2d34504d0d0a436c6f7365643a204d6f6e64617973', 28, 'world_map', None),
    ('ui.start.0fc860', 1034336, (1036636, 1036640), '456c6c656e277320486f757365', 28, 'world_map', None),
    ('ui.start.0fc870', 1034352, (1036656, 1036660), '4d61796f72277320486f757365', 28, 'world_map', None),
    ('ui.start.0fc880', 1034368, (1036676,), '53757065726d61726b65740d0a486173206d616e79207468696e67732c20696e636c7564696e67200d0a536565647320616e6420696e6772656469656e74732e', 28, 'world_map', None),
    ('ui.start.0fc8c4', 1034436, (1036680,), '53757065726d61726b65740d0a486f7572733a2039414d2d35504d0d0a436c6f7365643a2054756573646179732c2053756e64617973', 28, 'world_map', None),
    ('ui.start.0fc8fc', 1034492, (1036696,), '4d696e6572616c20436c696e69630d0a476574206578616d696e6564206f72206275792064727567732e', 28, 'world_map', None),
    ('ui.start.0fc928', 1034536, (1036700,), '4d696e6572616c20436c696e69630d0a486f7572733a2039414d2d34504d0d0a436c6f7365643a205765646e657364617973', 28, 'world_map', None),
    ('ui.start.0fc95c', 1034588, (1036716,), '4368757263680d0a57656464696e67732c2066756e6572616c7320616e6420616c736f0d0a636f6e66657373696f6e616c732061726520686572652e', 28, 'world_map', None),
    ('ui.start.0fc99c', 1034652, (1036720,), '4368757263680d0a54696d653a203130414d2d37504d', 28, 'world_map', None),
    ('ui.start.0fc9b4', 1034676, (1036736,), '416a612057696e6572790d0a44756b6520616e642068697320776966652073656c6c200d0a626f7468206a7569636520616e642077696e652e', 28, 'world_map', None),
    ('ui.start.0fc9f0', 1034736, (1036740,), '416a612057696e6572790d0a486f7572733a203130414d2d4e6f6f6e0d0a436c6f7365643a20536174757264617973', 28, 'world_map', None),
    ('ui.start.0fca20', 1034784, (1036756, 1036760), '44756b6527732043656c6c6172', 28, 'world_map', None),
    ('ui.start.0fca30', 1034800, (1036776,), '446f7567277320496e6e2e20446f75672073657276657320666f6f640d0a647572696e67207468652064617920616e64206c6971756f722061740d0a6e696768742e20486520616c736f2068617320612070686f6e652e', 28, 'world_map', None),
    ('ui.start.0fca88', 1034888, (1036780,), '446f7567277320496e6e0d0a486f7572733a2038414d2d39504d0d0a436c6f7365643a204e65766572', 28, 'world_map', None),
    ('ui.start.0fcab4', 1034932, (1036796,), '4861727665737420537072697465732720486f6d650d0a4120736d616c6c20686f75736520626568696e6420746865200d0a4368757263682e', 28, 'world_map', None),
    ('ui.start.0fcaf0', 1034992, (1036800,), '4861727665737420537072697465732720486f7573650d0a54696d653a2039414d2d36504d', 28, 'world_map', None),
    ('ui.start.0fcb18', 1035032, (1036816,), '5a61636b277320486f7573650d0a546865206d65726368616e7420576f6e20616c736f200d0a6c6976657320686572652e', 28, 'world_map', None),
    ('ui.start.0fcb4c', 1035084, (1036820,), '5a61636b277320486f757365', 28, 'world_map', None),
    ('ui.start.0fcb5c', 1035100, (1036836,), '4b616927732053656173696465204c6f6467650d0a4f70656e206f6e6c7920696e2053756d6d6572', 28, 'world_map', None),
    ('ui.start.0fcb88', 1035144, (1036840,), '4b616927732053656173696465204c6f6467650d0a486f7572733a203131414d2d31504d0d0a2020202020202035504d2d37504d', 28, 'world_map', None),
    ('ui.start.0fcbc0', 1035200, (1036856,), '536169626172612074686520426c61636b736d6974680d0a4d616b6573206d616e79207468696e677320666f7220796f750d0a696620796f7520676976652068696d20746865204f72652e', 28, 'world_map', None),
    ('ui.start.0fcc0c', 1035276, (1036860,), '536169626172612074686520426c61636b736d6974680d0a486f7572733a203130414d2d34504d0d0a436c6f7365643a20546875727364617973', 28, 'world_map', None),
    ('ui.start.0fcc48', 1035336, (1036876,), '596f64656c204661726d0d0a53656c6c7320436f777320616e642053686565702e', 28, 'world_map', None),
    ('ui.start.0fcc6c', 1035372, (1036880,), '596f64656c204661726d0d0a486f7572733a203130414d2d33504d0d0a436c6f7365643a204d6f6e64617973', 28, 'world_map', None),
    ('ui.start.0fcc9c', 1035420, (1036896,), '506f756c747279204661726d0d0a53656c6c7320436869636b656e732e', 28, 'world_map', None),
    ('ui.start.0fccbc', 1035452, (1036900,), '506f756c747279204661726d0d0a486f7572733a203131414d2d34504d0d0a436c6f7365643a2053756e64617973', 28, 'world_map', None),
    ('ui.start.0fccec', 1035500, (1036916,), '576f6f64637574746572277320486f7573650d0a53656c6c73204c756d6265722c20616e642063616e200d0a657870616e6420796f757220686f7573652e', 28, 'world_map', None),
    ('ui.start.0fcd2c', 1035564, (1036920,), '576f6f64637574746572277320486f7573650d0a486f7572733a203131414d2d34504d0d0a436c6f7365643a20536174757264617973', 28, 'world_map', None),
    ('ui.start.0fcd64', 1035620, (1036936,), '4c616b65204d696e650d0a596f752063616e206d696e65206d616e790d0a7468696e677320686572652e', 28, 'world_map', None),
    ('ui.start.0fcd90', 1035664, (1036940,), '4c616b65204d696e65', 28, 'world_map', None),
    ('ui.start.0fcd9c', 1035676, (1036956,), '537072696e67204d696e650d0a596f752063616e206d696e65206d616e790d0a7468696e677320686572652e', 28, 'world_map', None),
    ('ui.start.0fcdcc', 1035724, (1036960,), '537072696e67204d696e65', 28, 'world_map', None),
    ('ui.start.0fcdd8', 1035736, (1036976,), '486f7420537072696e670d0a52656375706572617465205374616d696e6120616e640d0a466174696775652e', 28, 'world_map', None),
    ('ui.start.0fce08', 1035784, (1036980,), '486f7420537072696e67', 28, 'world_map', None),
    ('ui.start.0fce18', 1035800, (1037016,), '4e6f7274682053696465206f66204d696e6572616c20546f776e0d0a4c6f7473206f662073686f707320616e6420686f6d65732e', 28, 'world_map', None),
    ('ui.start.0fce50', 1035856, (1037020,), '4e6f7274682053696465206f66204d696e6572616c20546f776e', 28, 'world_map', None),
    ('ui.start.0fce6c', 1035884, (1037036,), '52656172206f66204368757263680d0a4861727665737420537072697465732720686f6d65200d0a697320686572652e', 28, 'world_map', None),
    ('ui.start.0fcea0', 1035936, (1037040,), '52656172206f6620436875726368', 28, 'world_map', None),
    ('ui.start.0fceb0', 1035952, (1037056,), '526f7365205371756172650d0a4d616e79206576656e7473206172652068656c6420686572652e', 28, 'world_map', None),
    ('ui.start.0fced8', 1035992, (1037060,), '526f736520537175617265', 28, 'world_map', None),
    ('ui.start.0fcee4', 1036004, (1037076,), '4d696e6572616c2042656163680d0a426561636820486f757365206973206f70656e200d0a696e2053756d6d65722e205a61636b206c6976657320686572652e', 28, 'world_map', None),
    ('ui.start.0fcf28', 1036072, (1037080,), '4d696e6572616c204265616368', 28, 'world_map', None),
    ('ui.start.0fcf38', 1036088, (1037096, 1037116), '536f7574682053696465206f66204d696e6572616c20546f776e0d0a596f64656c204661726d2c20506f756c747279204661726d2c200d0a616e6420426c61636b736d6974682061726520686572652e', 28, 'world_map', None),
    ('ui.start.0fcf8c', 1036172, (1037100, 1037120), '536f7574682053696465206f66204d696e6572616c20546f776e', 28, 'world_map', None),
    ('ui.start.0fcfa8', 1036200, (1037136, 1037156), '466f726573740d0a54686520576f6f64637574746572277320486f7573650d0a697320686572652e', 28, 'world_map', None),
    ('ui.start.0fcfd4', 1036244, (1037140, 1037160), '466f72657374', 28, 'world_map', None),
    ('ui.start.0fcfdc', 1036252, (1037176,), '5065616b206f66204d6f7468657227732048696c6c0d0a54686572652773206120677265617420766965770d0a66726f6d20686572652e', 28, 'world_map', None),
    ('ui.start.0fd014', 1036308, (1037180,), '5065616b206f66204d6f7468657227732048696c6c', 28, 'world_map', None),
    ('ui.start.0fd02c', 1036332, (1037196,), '4d6f7468657227732048696c6c0d0a546865204861727665737420476f646465737320697320736169640d0a746f206c69766520696e2074686520737072696e672e', 28, 'world_map', None),
    ('ui.start.0fd070', 1036400, (1037200,), '4d6f7468657227732048696c6c', 28, 'world_map', None),
    ('ui.start.0fc6e8', 1033960, (494100,), '204661726d', 10, 'world_map', None),
    ('ui.start.0fbee0', 1031904, (468168,), '4d696e692d47616d65205265636f7264732081a181a181a181a1', 26, 'statistics', None),
    ('ui.start.0fbf3c', 1031996, (472068,), '496e636f6d652f457870656e7365732081a181a181a181a181a1', 26, 'statistics', None),
    ('ui.start.0fbf84', 1032068, (474272,), '4c6f6e67657374206c6976696e6720616e696d616c2081a181a1', 26, 'statistics', None),
    ('ui.start.0fbfcc', 1032140, (477996,), '4c6f77657374204c6576656c20696e204d696e6581a181a181a1', 26, 'statistics', None),
    ('ui.start.11561c', 1136156, (1136592,), '55736566756c20436f6e74726f6c73', 28, 'useful_controls', None),
    ('ui.start.11562c', 1136172, (1136596,), '4f70656e20546f776e204d6170', 28, 'useful_controls', None),
    ('ui.start.11563c', 1136188, (1136600,), '5072657373205374617274207768696c6520686f6c64696e67', 28, 'useful_controls', None),
    ('ui.start.115658', 1136216, (1136604, 1136620), '646f776e20746865204c20427574746f6e2e', 28, 'useful_controls', None),
    ('ui.start.11566c', 1136236, (1136612,), '4f70656e204661726d204d6170', 28, 'useful_controls', None),
    ('ui.start.11567c', 1136252, (1136616,), '50726573732053656c656374207768696c6520686f6c64696e67', 28, 'useful_controls', None),
    ('ui.start.115698', 1136280, (1136628,), '53776974636820546f6f6c73', 28, 'useful_controls', None),
    ('ui.start.1156a8', 1136296, (1136632,), '5769746820656d7074792068616e64732c', 28, 'useful_controls', None),
    ('ui.start.1156bc', 1136316, (1136636,), '707265737320746865204220427574746f6e207768696c6520', 28, 'useful_controls', None),
    ('ui.start.109884', 1087620, (1136640,), '686f6c64696e6720646f776e20746865204c20427574746f6e2e', 28, 'useful_controls', None),
    ('ui.start.1156d8', 1136344, (1136648,), '4f70656e20546f6f6c7320616e64204974656d2053637265656e', 28, 'useful_controls', None),
    ('ui.start.1156f4', 1136372, (1136652,), '507265737320746865204220427574746f6e207768696c65', 28, 'useful_controls', None),
    ('ui.start.115710', 1136400, (1136656,), '686f6c64696e6720646f776e20746865204120427574746f6e2e', 28, 'useful_controls', None),
    ('ui.start.11572c', 1136428, (1136664,), '507574204974656d2041776179', 28, 'useful_controls', None),
    ('ui.start.11573c', 1136444, (1136668,), '507265737320746865204220427574746f6e', 28, 'useful_controls', None),
    ('ui.start.115750', 1136464, (1136672,), '7768656e20686f6c64696e6720736f6d657468696e672c', 28, 'useful_controls', None),
    ('ui.start.115768', 1136488, (1136676,), '202a457863657074207768656e205275636b7361636b', 28, 'useful_controls', None),
    ('ui.start.115780', 1136512, (1136680,), '2069732066756c6c2e', 28, 'useful_controls', None),
    ('ui.start.11578c', 1136524, (1136688,), '43616c6c204f757420746f20506572736f6e', 28, 'useful_controls', None),
    ('ui.start.1157a0', 1136544, (1136692,), '5072657373204c20427574746f6e207768656e20', 28, 'useful_controls', None),
    ('ui.start.1157b8', 1136568, (1136696,), '6e6f7420686f6c64696e6720616e797468696e672e', 28, 'useful_controls', None),
)


def extract_records(rom):
    verify_bag(rom)
    if rom[BOOK_TITLE_SITE:BOOK_TITLE_SITE+10] != BOOK_TITLE_EXPECTED:
        raise FormatError('book title byte loop mismatch')
    rows = []
    for identifier,address,slots,expected,columns,group,limit in SPECS:
        raw = cstring(rom,address,address+512)
        if raw.hex() != expected or any(u32(rom,p) != ROM_BASE+address for p in slots):
            raise FormatError('START menu source/pointer mismatch: '+identifier)
        row = make_record(identifier,raw,address,'start_menu_'+group,
            {'kind':'pointer','pointer_offsets':list(slots),
             'reference':'StanHash/fomt b8471ae asm/new_game.s (Diary); asm/code_0803EE94.s (bag/statistics/map); map descriptor table 080FD080 stride20'},columns)
        if limit is not None:row['max_encoded_bytes'] = limit
        rows.append(row)
    return rows

# char title[12] at +0x28C; next field at +0x298 (080CAFC4).
BAG_EXPECTED = {0xCB05A:bytes.fromhex('082c'),0xCB05E:bytes.fromhex('0824'),
                0xCB178:bytes.fromhex('08f0fefcc0004022'),
                0xCC1F8:bytes.fromhex('082c'),0xCC1FC:bytes.fromhex('0824'),
                0xCC414:bytes.fromhex('07f0b0fbc0004022')}

def verify_bag(rom):
    if any(rom[at:at+len(data)] != data for at,data in BAG_EXPECTED.items()):
        raise FormatError('bag title byte buffer/width instructions mismatch')


def bag_width_hook(address, resume=0x080CB181):
    """Replace strlen*8 with native single-/double-byte glyph count*8."""
    from keystone import Ks,KS_ARCH_ARM,KS_MODE_THUMB
    asm = '''
        mov r1, r0
        movs r0, #0
    loop:
        ldrb r2, [r1]
        cmp r2, #0
        beq done
        adds r1, #1
        adds r0, #1
        cmp r2, #0x81
        blo loop
        cmp r2, #0x9f
        bls double_byte
        cmp r2, #0xe0
        blo loop
        cmp r2, #0xfc
        bhi loop
    double_byte:
        cmp r2, #0xeb
        beq skip
        adds r0, #1
    skip:
        adds r1, #1
        b loop
    done:
        lsls r0, r0, #3
        movs r2, #64
        ldr r3, resume
        bx r3
        .align 2
    resume: .word 0x080CB181
    '''
    asm = asm.replace("0x080CB181",hex(resume))
    return bytes(Ks(KS_ARCH_ARM,KS_MODE_THUMB).asm(asm,addr=address)[0])

BOOK_TITLE_SITE = 0x7A216
BOOK_TITLE_EXPECTED = bytes.fromhex('684640190c300478002c')
BOOK_TITLE_ID = 'ui.start.11561c'


def book_title_hook(address, string_address, cache_address, cells):
    """Only the Useful Controls title uses a cell cache; other books fall back.

Original 0807A216 loop indexes one byte per OBJ glyph. Cache keeps the same
8x16 cells, allocation, palette and VRAM upload at 0807A252.
"""
    from keystone import Ks,KS_ARCH_ARM,KS_MODE_THUMB
    asm = f'''
        mov r0, r9
        ldr r1, book_field
        adds r0, r0, r1
        ldr r0, [r0]
        ldr r0, [r0]
        ldr r1, title_pointer
        cmp r0, r1
        bne native
        cmp r5, #{cells}
        bhs finish
        ldr r0, cache_pointer
        lsls r1, r5, #6
        adds r0, r0, r1
        add r1, sp, #0x34
        movs r2, #16
    copy:
        ldr r3, [r0]
        str r3, [r1]
        adds r0, #4
        adds r1, #4
        subs r2, #1
        bne copy
        ldr r3, upload
        bx r3
    finish:
        ldr r3, exit_loop
        bx r3
    native:
        mov r0, sp
        adds r0, r0, r5
        adds r0, #12
        ldrb r4, [r0]
        cmp r4, #0
        ldr r3, native_resume
        bx r3
        .align 2
    book_field: .word 0xA5C
    title_pointer: .word {string_address}
    cache_pointer: .word {cache_address}
    upload: .word 0x0807A253
    exit_loop: .word 0x0807A279
    native_resume: .word 0x0807A221
    '''
    return bytes(Ks(KS_ARCH_ARM,KS_MODE_THUMB).asm(asm,addr=address)[0])
