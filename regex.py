#encoding: utf8

import logging

class Link(object):
    def __init__(self):
        self.link = None

class State(object):
    Char, Switch, End = range(3)

    def __init__(self):
        self.char = None
        self.type = None
        self.out1 = Link()
        self.out2 = Link()

    @staticmethod
    def createChar(c):
        s = State()
        s.type = State.Char
        s.char = c
        return s

    @staticmethod
    def createSwitch():
        s = State()
        s.type = State.Switch
        return s

    @staticmethod
    def createMatch():
        s = State()
        s.type = State.End
        return s

    def __str__(self):
        if self.type == State.End:
            return 'MATCHSTATE'
        elif self.type == State.Char:
            return 'CHAR(' + self.char + ')'
        elif self.type == State.Switch:
            return 'SWITCH'

MATCHSTATE = State.createMatch()

class Fragment(object):
    def __init__(self, state, outs):
        self.start = state
        self.outs = outs

    def connect_to(self, state):
        for o in self.outs:
            o.link = state

    def print_self(self):
        print self.start
        for o in self.outs:
            print o.link

def parse_postfix(rgx):
    stack = []
    for c in rgx:
        logging.debug("Processing char: %s", c)
        if c == '.':
            logging.debug("Found concatenation, joining last two fragments")
            e2 = stack.pop()
            e1 = stack.pop()
            e1.connect_to(e2.start)
            stack.append(Fragment(e1.start, e2.outs))
        elif c == '|':
            logging.debug("Found alteration, creating switch for last two fragments")
            e2 = stack.pop()
            e1 = stack.pop()
            state = State.createSwitch()
            state.out1.link = e1.start
            state.out2.link = e2.start
            outs = [e for e in e1.outs]
            outs.extend(e2.outs)
            stack.append(Fragment(state, outs))
        elif c == '?':
            logging.debug("Found zero or one, creating switch")
            e1 = stack.pop()
            state = State.createSwitch()
            state.out1.link = e1.start
            outs = [state.out2]
            outs.extend(e1.outs)
            stack.append(Fragment(state, outs))
        elif c == '*':
            logging.debug("Found zero or more, creating switch")
            e1 = stack.pop()
            state = State.createSwitch()
            state.out1.link = e1.start
            e1.connect_to(state)
            stack.append(Fragment(state, [state.out2]))
        elif c == '+':
            logging.debug("Found one or more, creating switch")
            e1 = stack.pop()
            state = State.createSwitch()
            state.out1.link = e1.start
            e1.connect_to(state)
            stack.append(Fragment(e1.start, [state.out2]))
        else:
            logging.debug('Found common char, creating char fragment')
            state = State.createChar(c)
            stack.append(Fragment(state, [state.out1]))
    e = stack.pop()
    if len(stack) > 0:
        raise RuntimeError('Unable to compile regex')
    e.connect_to(MATCHSTATE)
    return e

class StateList(object):
    def __init__(self):
        self.states = {}

    def isMatch(self):
        return any(s == MATCHSTATE for s in self.states)

    def clear(self):
        self.states = {}

    def addState(self, state):
        if state == None or state in self.states:
            return
        self.states[state] = True
        if state.type == State.Switch:
            self.addState(state.out1.link)
            self.addState(state.out2.link)

    def dump(self):
        logging.debug("<StateList.states>: " + ', '.join(str(s) for s in self.states))

def match(pattern, string):
    logging.debug("Trying to match string '%s' vs pattern '%s'", string, pattern)
    logging.debug("Compiling regex")
    fragment = parse_postfix(pattern)
    clist = StateList()
    nlist = StateList()
    clist.addState(fragment.start)
    logging.debug("Matching string")
    for i, c in enumerate(string):
        logging.debug("Step %d: processing character '%s' of input string", i + 1, c)
        clist.dump()
        step(clist, nlist, c)
        clist, nlist = nlist, clist
        clist.dump()
    return clist.isMatch()

def step(clist, nlist, c):
    nlist.clear()
    for state in clist.states:
        if state.char == c:
            nlist.addState(state.out1.link)

