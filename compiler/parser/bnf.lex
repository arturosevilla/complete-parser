# Backus Naur tokens
<[a-zA-Z_][A-Z\-0-9a-z_]*>	RULE_NAME
::=				RULE_DEFINITION
\|				OR
"[a-zA-Z_][A-Z\-0-9a-z_]*"	RULE_TERMINAL
""				EMPTY

# other commands
%import				IMPORT_COMMAND
[.a-zA-Z_/][.a-zA-Z_/]*		IMPORT_ARGUMENT

