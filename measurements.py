###############################################################################
## 
## measurements.py
##
##   Class for working with individual measurements, measurement ranges, and
##   measurement collections.
##
##

import re

###############################################################################
##

class Measurement():
    '''
    Class for creating, representing, and normalizing individual measurements
    as quantities.
    '''
    def __init__(self, raw, notation):
        self.raw = raw
        self.notation = notation
        self.cm = None
        self.inches = None

    def set_unit(self, unit):
        '''
        Use the unit information to parse the raw string
        representation into a numerical data type.
        '''
        if self.notation == 'prime_double_prime':
            (feet, inches) = self.raw.split("'")
            inches = inches[:-1] if inches[-1] == '"' else inches
            self.inches = (float(feet)*12) + (float(inches))
            self.cm = self.inches * 2.54
        elif self.notation == 'prime':
            self.inches = float(self.raw[0:-1])*12
            self.cm = self.inches * 2.54
        elif self.notation == 'decimal_mixed' and unit == "in":
            (term, frac) = self.raw.strip().split(" ")
            (numerator, denominator) = frac.split("/")
            self.inches = (float(term)*float(denominator) + float(numerator))/float(denominator)
            self.cm = self.inches * 2.54
        elif self.notation == 'mixed' and unit == "in":
            (term, frac) = self.raw.strip().split(" ")
            (numerator, denominator) = frac.split("/")
            self.inches = (float(term)*float(denominator) + float(numerator))/float(denominator)
            self.cm = self.inches * 2.54
        elif self.notation == 'fraction' and unit == "in":
            (numerator, denominator) = self.raw.split("/")
            self.inches = float(numerator)/float(denominator)
            self.cm = self.inches * 2.54
        elif self.notation in ['decimal', 'integer'] and unit == "mm":
            self.cm = float(self.raw)*0.1
            self.inches = float(self.raw) / 25.4
        elif self.notation in ['decimal', 'integer'] and unit == "cm":
            self.cm = float(self.raw)
            self.inches = self.cm / 2.54
        elif self.notation in ['decimal', 'integer'] and unit == "m":
            self.cm = float(self.raw)*100
            self.inches = self.cm / 2.54
        elif self.notation in ['decimal', 'integer'] and unit == "in":
            self.cm = float(self.raw)*2.54
            self.inches = float(self.raw)
        elif self.notation in ['decimal', 'integer'] and unit == "ft":
            self.cm =  float(self.raw)*30.48
            self.inches = float(self.raw)*12
        else:
            return False

        # One of the non-else branches above succeeded.
        return True

    def __str__(self):
        return str(self.cm)

    def __repr__(self):
        return str(self.cm)

    def __eq__(self, other):
        if self.cm is None or other.cm is None:
            raise Exception()
        return self.cm == other.cm

    def __lt__(self, other):
        if self.cm is None or other.cm is None:
            raise Exception()
        return self.cm < other.cm

    def __lte__(self, other):
        if self.cm is None or other.cm is None:
            raise Exception()
        return self.cm <= other.cm

    def __gt__(self, other):
        if self.cm is None or other.cm is None:
            raise Exception()
        return self.cm > other.cm

    def __gte__(self, other):
        if self.cm is None or other.cm is None:
            raise Exception()
        return self.cm >= other.cm

    def __max__(self, other):
        return self.cm if self.cm >= other.cm else other.cm

    def __min__(self, other):
        return self.cm if self.cm <= other.cm else other.cm

class Assortment():
    '''
    Class for creating, representing, and normalizing and
    assortment of explicit measurement quantities.
    '''
    def __init__(self):
        self.measurements = []

    def __bool__(self):
        return len(self.measurements) > 0

    def add(self, measurement):
        self.measurements.append(measurement)

    def set_unit(self, unit):
        result = all([m.set_unit(unit) for m in self.measurements])
        if result:
            self.measurements.sort()
        return result

    def raws(self):
        return [m.raw for m in self.measurements]

    def notations(self):
        return [m.notation for m in self.measurements]

    def min(self):
        return min(self.measurements)

    def max(self):
        return max(self.measurements)
    
#eof