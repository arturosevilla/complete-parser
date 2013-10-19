# Backus Naur tokens
<[a-zA-Z_][A-Z\-0-9a-z_]*>	RULE_NAME
::=				RULE_DEFINITION
\|				OR
"[a-zA-Z_][A-Z\-0-9a-z_]*"	RULE_TERMINAL
""				EMPTY
