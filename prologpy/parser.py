import re
from .interpreter import Conjunction, Variable, Term, TRUE, Rule
import regex

TOKEN_REGEX = r"[A-Za-z0-9_]+|:\-|[()\.,]"
# Atom大文字小文字アンダーバーに加えて日本語の文字種
ATOM_NAME_REGEX = r"^[A-Za-z0-9_]+$"
ATOM_NAME_REGEX_JAPANESE = r"^[A-Za-z0-9_ａ-ｚＡ-Ｚ０-９，．、。\p{Han}\p{Katakana}\p{Hiragana}]+$"
VARIABLE_REGEX = r"^[A-Z_][A-Za-z0-9_]*$"   # 変数大文字 _などからスタート
VARIABLE_REGEX_JP = r"^[A-Z_].*$"           # 変数は大文字または _ からの文字

# Regex to parse comment strings. The first group captures quoted strings (
# double and single). The second group captures regular comments ('%' for
# single-line or '/* */' for multi-line)
COMMENT_REGEX = r"(\".*?\"|\'.*?\')|(/\*.*?\*/|%[^\r\n]*$)"

def parse_tokens_from_string_jp(input_text):
    # Convert the input text into a list of tokens we can iterate over / process

    no_comment_text = remove_comments(input_text)
    no_comment_text = no_comment_text.strip()
    # . で分割．:- で分割． => すべて pred(X,Y),a(X),b(Y).  の形
    def make_tokens (text):
        text = "".join(text.split())  #文字列の空白を消す
        parts = text.split(':-') #2文字なので先に切る．ただし切ってから加える
        parts = [x + ':-' for x in parts]
        parts[-1] = parts[-1].replace(':-','')
        out = []
        p = re.compile(r'[().,|\[\]]')
        for part in parts:
            out_part = ''
            for c in part:
                #if previous_character == ')' and p2.match(c):   # ), などにマッチした
                #    out.append('') # ), と ). のときに '' 空文字入れる
                #    out.append(c)  #区切りも保存
                #    out_part = ''
                if p.match(c):  #1文字の区切りにマッチした
                    if out_part != '':
                        out.append(out_part)
                    out.append(c)  #区切りも保存
                    out_part = ''  #必ず最後はここを通る
                else:
                    out_part += c #なにもないと連結 
            if out_part != '': #末尾に:- がくる時なので足す
                out.append(out_part)
        return out #もしここで out_partになにか残ってたらダメ
    token_out = make_tokens(no_comment_text)
    return token_out

def remove_comments(input_text):
    """Return the input text string with all of the comments removed from it"""

    # Create a regular expression Pattern object we can use to find and strip out
    # comments. The MULTILINE flag tells Python to treat each line in the string
    # separately, while the DOTALL flag indicates that we can match patterns
    # which span multiple lines (so our multi-line comments '/* */' can  be
    # processed)
    regex = re.compile(COMMENT_REGEX, re.MULTILINE | re.DOTALL)

    def remove_comment(match):
        """If we found a match for our 2nd group, it is a comment, so we remove"""
        if match.group(2) is not None:
            return ""
        # Otherwise, we found a quoted string containing a comment, so we leave
        # it in
        else:
            return match.group(1)

    return regex.sub(remove_comment, input_text)


def parse_tokens_from_string(input_text):
    """Convert the input text into a list of tokens we can iterate over / process"""
    iterator = re.finditer(TOKEN_REGEX, remove_comments(input_text))
    return [token.group() for token in iterator]


class Parser(object):
    """
    NOTE: Instance can only be used once!
    """

    def __init__(self, input_text):
        self._tokens = parse_tokens_from_string_jp(input_text)
        self._scope = None

    def parse_rules(self):
        rules = []
        while self._tokens:
            self._scope = {}
            rules.append(self._parse_rule())
        return rules

    def parse_query(self):
        self._scope = {}
        return self._parse_term()

    @property
    def _current(self):
        return self._tokens[0]

    def _pop_current(self):
        return self._tokens.pop(0)

    def _parse_atom(self):
        name = self._pop_current()
        if regex.compile(ATOM_NAME_REGEX_JAPANESE).fullmatch(name) is False:
            raise Exception("Invalid Atom Name: " + str(name))
        return name

    def _parse_term(self):
        # If we encounter an opening parenthesis, we know we're dealing with a
        # conjunction, so we process the list of arguments until we hit a closing
        # parenthesis and return the conjunction object.

        # ここで単なる述語または定数(atom) か変数を分けている

        if self._current == "(":
            self._pop_current()
            arguments = self._parse_arguments()
            return Conjunction(arguments)

        functor = self._parse_atom()

        # If we have a matching variable, we make sure that variables with the same
        # name within a rule always use one variable object (with the exception of
        # the anonymous '_' variable object).
        if re.match(VARIABLE_REGEX, functor) is not None:

            if functor == "_":
                return Variable("_")

            variable = self._scope.get(functor)

            if variable is None:
                self._scope[functor] = Variable(functor)
                variable = self._scope[functor]

            return variable

        # If there are no arguments to process, return an atom. Atoms are processed
        # as terms without arguments.
        if self._current != "(":
            return Term(functor)
        self._pop_current()
        arguments = self._parse_arguments()
        return Term(functor, arguments)

    def _parse_arguments(self):
        arguments = []
        # Keep adding the arguments to our list until we encounter an ending
        # parenthesis ')'
        while self._current != ")":
            arguments.append(self._parse_term())
            if self._current not in (",", ")"):
                raise Exception(
                    "Expected , or ) in term but got " + str(self._current)
                )
            if self._current == ",":
                self._pop_current()
        self._pop_current()
        return arguments

    def _parse_rule(self): #バラバラlistにした入力ルールを分類

        head = self._parse_term()

        if self._current == ".":
            self._pop_current()
            # We process facts as rules with the tail set to true:
            return Rule(head, TRUE())

        if self._current != ":-":
            raise Exception(
                "Expected :- in rule but got " + str(self._current)
            )

        self._pop_current()

        # Process the rule arguments
        arguments = []

        while self._current != ".":
            arguments.append(self._parse_term())

            if self._current not in (",", "."):
                raise Exception(
                    "Expected , or . in term but got " + str(self._current)
                )

            if self._current == ",":
                self._pop_current()

        self._pop_current()

        # If we have more than one argument, we return a conjunction, otherwise,
        # we process the item as a regular rule containing a head and a tail
        tail = arguments[0] if arguments == 1 else Conjunction(arguments)
        return Rule(head, tail)
