
from typing import List, TypeVar

class CombinedList:
    '''
    Helper class for handling 2 lists as 1, does not support modification of the lists
    also slices are a bit fucky so undefined behaviour when usin them is a near certainty
    '''

    def __init__(self, first: List[object], second: List[object]):
        
        self.first = first
        self.second = second

        self.length = len(first) + len(second)

    def __getitem__(self, idx: int | slice) -> object:
        '''
        Return the item specified by the index into both lists

        Return:
            T: Object at the index

        Raises:
            IndexError
        '''

        if isinstance(idx, slice):
            
            result: List[object] = []
            
            if idx.start is not None and idx.start < 0:
                raise BaseException('A negative start in CombinedList slices results in UB')

            for i in range(idx.start if idx.start is not None else 0, 
                           idx.stop  if idx.stop  is not None else self.length, 
                           idx.step  if idx.step  is not None else 1):

                if i >= self.length:
                    raise IndexError("Index out of range of CombinedList")

                if i < len(self.first):
                    result.append(self.first[i])

                else:
                    result.append(self.second[i - len(self.first)])

            return result
        
        if idx < 0:
            idx %= self.length 

        if 0 <= idx and idx < self.length:

            if idx < len(self.first):
                return self.first[idx]

            else:
                return self.second[idx - len(self.first)]

        raise IndexError("Index out of range of CombinedList")
    
    def __len__(self):
        return self.length

class CombinedListIter:
    
    def __init__(self, first, second):

        self.lists = [iter(first) + iter(second)]

    def __iter__(self):
        return self

    def __next__(self):
        
        for lst in self.lists:
            
            try:
                return next(lst)
            except StopIteration:
                pass

        raise StopIteration
