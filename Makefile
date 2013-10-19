
all: flexer.py parser/bnf.lex
	python flexer.py parser/bnf.lex > parser/bnf_lexer.py

clean:
	rm parser/bnf_lexer.py
