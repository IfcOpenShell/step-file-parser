# Step Physical File Validator

Pure-python Step Physical File Validator and Parser implemented using Lark  (`pip install -r requirements.in`).

## Example command line usage:

~~~
$ python main.py fixtures\fail_double_comma.ifc
On line 8 column 21:
Unexpected comma (',')
Expecting one of DBLQUOTE DOT HASH INT LPAR NONE QUOTE REAL STAR UPPER
00008 | #1=IFCPERSON($,$,'',,$,$,$,$);
                            ^

$ python main.py fixtures\fail_double_semi.ifc
On line 27 column 66:
Unexpected semicolon (';')
Expecting one of ENDSEC HASH
00027 | #20=IFCPROJECT('2AyG2X0sb16Bjd4gQc07yZ',#5,'',$,$,$,$,(#11),#19);;
                                                                         ^

$ python main.py fixtures\fail_duplicate_id.ifc
On line 27:
Duplicate instance name #19
00027 | #19=IFCPROJECT('2AyG2X0sb16Bjd4gQc07yZ',#5,'',$,$,$,$,(#11),#19);
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

$ python main.py fixtures\fail_no_header.ifc
On line 2 column 1:
Unexpected hex ('F')
Expecting HEADER
00002 | FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
        ^

$ python main.py fixtures\pass_1.ifc
Valid
~~~
