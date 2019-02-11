# -*- coding: utf-8 -*-
import logging
import spacy

class NLPEngine(object):

    def __init__(self):
        self.nlp = spacy.load('en_core_web_lg')

    ## List Manipulation
    def _flattenList(self, l):
        return [str(item) for sublist in l for item in sublist]

    def _flattenNonEmpty(self, l):
        nonEmpty = [a for a in l if len(a) > 0]
        nonEmpty = self._flattenList(nonEmpty)
        return nonEmpty

    def _textFromTokenList(self, tokenList):
        if type(tokenList) != list:
            return tokenList
        return " ".join([str(token) for token in tokenList])

    ## Predicates
    def _isNoun(self, token):
        return token.pos_ in ["NOUN", "PROPN", "NUM"]

    def _isCopularVerb(self, token):
        return token.pos_ == "VERB" and token.text in ["is", "was", "are", "were"]

    ## Traversal
    def _traverseVerbCompound(self, verb):
        prefix = [child for child in verb.children if child.dep_ in ["advmod", "aux", "neg"]]
        suffix = [child for child in verb.children if child.dep_ in ["prt"]]
        return prefix + [verb] + suffix

    def _traverseNounCompounds(self, noun):
        if not self._isNoun(noun):
            return [noun]
        
        leftTreeModifiers = ["poss", "det", "compound", "amod", "advmod", "nummod", "nmod"]
        rightTreeModifiers = ["poss", "det", "compound", "amod", "nummod", "case", "appos"]

        leftTree = [child for child in noun.children if child.i < noun.i and child.dep_ in leftTreeModifiers]
        rightTree = [child for child in noun.children if child.i > noun.i and child.dep_ in rightTreeModifiers]
        
        leftTreePrefix = []
        for child in leftTree:
            result = self._traverseNounCompounds(child)
            leftTreePrefix = leftTreePrefix + result
        
        rightTreeSuffix = []
        for child in rightTree:
            result = self._traverseNounCompounds(child)
            rightTreeSuffix = rightTreeSuffix + result
        
        leftTreePrefix.sort(key=lambda x: x.i)
        rightTreeSuffix.sort(key=lambda x: x.i)
        
        return leftTreePrefix + [noun] + rightTreeSuffix

    def _nounCC(self, noun):
        conjs = [child for child in noun.children if child.dep_ in ["conj"]]
        ccs = [child for child in noun.children if child.dep_ in ["cc"]]
        
        if len(conjs) == 0:
            return []
        else:
            result = []
            for conj in conjs:
                result = ccs + self._traverseNounCompounds(conj) + self._nounCC(conj)

            return result

    def _depOfVerb(self, verb, dep):
        depList = [child for child in verb.children if child.dep_ == dep]
        
        if len(depList) == 0:
            return None
        return depList[0]

    def _traversePrepAndPobjs(self, token): # token is either noun or verb
        preps = [child for child in token.children if child.dep_ in ["agent", "prep"]]
        prepsAndPobjs = []    
        
        for prep in preps:
            pobjList = [child for child in prep.children if child.dep_ == "pobj"]
            if len(pobjList) == 0:
                continue
            else:
                prepsAndPobjs.append((prep, pobjList[0]))
            
        return prepsAndPobjs

    def _constructProcessTextResult(self, nsubj, predicate, dobj, prepPobj):
        result = {}
        fullTextList = []

        if nsubj != None:
            nsubjCompound = self._traverseNounCompounds(nsubj)
            fullTextList.append(nsubjCompound)
            result["subject"] = self._textFromTokenList(nsubjCompound)

        if nsubj != None:
            fullTextList.append(self._nounCC(nsubj))
            result["subject_conj"] = self._textFromTokenList([self._textFromTokenList(conj) for conj in self._nounCC(nsubj)])

        if predicate != None:
            predicateCompound = self._traverseVerbCompound(predicate)
            fullTextList.append(predicateCompound)
            result["predicate"] = self._textFromTokenList(predicateCompound)

        if dobj != None:
            dobjCompound = self._traverseNounCompounds(dobj)
            fullTextList.append(dobjCompound)
            result["object"] = self._textFromTokenList(dobjCompound)

        if dobj != None:
            fullTextList.append(self._nounCC(dobj))
            result["object_conj"] = self._textFromTokenList([self._textFromTokenList(conj) for conj in self._nounCC(dobj)])

        if prepPobj != None:
            ppCompounds = []
            for pp in prepPobj:
                pobj_compound = self._traverseNounCompounds(pp[1])
                ppCompounds.append([pp[0]] + pobj_compound)
            
            fullTextList.append(self._flattenNonEmpty(ppCompounds))
            result["pobj"] = self._textFromTokenList([self._textFromTokenList(pp) for pp in ppCompounds])

        result["full"] = " ".join(self._flattenNonEmpty(fullTextList))
        return result

    def _handleNonCopularVerb(self, verb):
        nsubj = self._depOfVerb(verb, "nsubj")

        if nsubj == None:
            return
        
        dobj = self._depOfVerb(verb, "dobj")
        if dobj != None:        
            prepAndPobjs = self._traversePrepAndPobjs(verb)
            if len(prepAndPobjs) == 0:
                return self._constructProcessTextResult(nsubj, verb, dobj, None)
            
            return self._constructProcessTextResult(nsubj, verb, dobj, prepAndPobjs)
            
        else:
            prepAndPobjs = self._traversePrepAndPobjs(verb)
            if len(prepAndPobjs) == 0:
                return       
            
            return self._constructProcessTextResult(nsubj, verb, None, prepAndPobjs)

    


    def processText(self, text):
        doc = self.nlp(text)

        # Step 1: Extract entities
        entities = {}
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "LOC", "PRODUCT", "ORG", "LAW", "GPE"]:
                entity = ent.text.strip()
                if len(entity) > 0:
                    if ent.label_ in entities and ent.text not in entities[ent.label_]:
                        entities[ent.label_].append(ent.text)
                    else:
                        entities[ent.label_] = [ent.text]

        # Step 2: Extract SPOLT
        spolt = []
        for sentence in doc.sents:
            if len(sentence.text.strip().split(" ")) < 3:
                continue

            s_doc = self.nlp(sentence.text.strip())
            for token in s_doc:
                if token.pos_ == "VERB" and not self._isCopularVerb(token):
                    data = self._handleNonCopularVerb(token)
                    if data != None:
                        spolt.append(data) 

        return entities, spolt
        