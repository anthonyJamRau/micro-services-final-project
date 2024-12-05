import pandas as pd

def return_policy():
    r1 = pd.Series({'2': 'Hit', '3': 'Hit', '4': 'Hit', '5': 'Hit','6': 'Hit', '7': 'Hit', '8': 'Hit','9': 'Hit','10': 'Hit','11': 'Hit'})
    r2 = pd.Series({'2': 'Hit', '3': 'Hit', '4': 'Hit', '5': 'Hit','6': 'Hit', '7': 'Hit', '8': 'Hit','9': 'Hit','10': 'Hit','11': 'Hit'})
    r3 = pd.Series({'2': 'Hit', '3': 'Hit', '4': 'Hit', '5': 'Hit','6': 'Hit', '7': 'Hit', '8': 'Hit','9': 'Hit','10': 'Hit','11': 'Hit'})
    r4 = pd.Series({'2': 'Hit', '3': 'Hit', '4': 'Hit', '5': 'Hit','6': 'Hit', '7': 'Hit', '8': 'Hit','9': 'Hit','10': 'Hit','11': 'Hit'})
    r5 = pd.Series({'2': 'Hit', '3': 'Hit', '4': 'Hit', '5': 'Hit','6': 'Hit', '7': 'Hit', '8': 'Hit','9': 'Hit','10': 'Hit','11': 'Hit'})
    r6 = pd.Series({'2': 'Hit', '3': 'Hit', '4': 'Hit', '5': 'Hit','6': 'Hit', '7': 'Hit', '8': 'Hit','9': 'Hit','10': 'Hit','11': 'Hit'})
    r7 = pd.Series({'2': 'Hit', '3': 'Hit', '4': 'Hit', '5': 'Hit','6': 'Hit', '7': 'Hit', '8': 'Hit','9': 'Hit','10': 'Hit','11': 'Hit'})
    r8 = pd.Series({'2': 'Hit', '3': 'Hit', '4': 'Hit', '5': 'Hit','6': 'Hit', '7': 'Hit', '8': 'Hit','9': 'Hit','10': 'Hit','11': 'Hit'})
    r9 = pd.Series({'2': 'Hit', '3': 'Hit', '4': 'Stand', '5': 'Stand','6': 'Stand', '7': 'Hit', '8': 'Hit','9': 'Hit','10': 'Hit','11': 'Hit'})
    r10 = pd.Series({'2': 'Stand', '3': 'Stand', '4': 'Stand', '5': 'Stand','6': 'Stand', '7': 'Hit', '8': 'Hit','9': 'Hit','10': 'Hit','11': 'Hit'})
    r11 = pd.Series({'2': 'Stand', '3': 'Stand', '4': 'Stand', '5': 'Stand','6': 'Stand', '7': 'Hit', '8': 'Hit','9': 'Hit','10': 'Hit','11': 'Hit'})
    r12 = pd.Series({'2': 'Stand', '3': 'Stand', '4': 'Stand', '5': 'Stand','6': 'Stand', '7': 'Hit', '8': 'Hit','9': 'Hit','10': 'Hit','11': 'Hit'})
    r13 = pd.Series({'2': 'Stand', '3': 'Stand', '4': 'Stand', '5': 'Stand','6': 'Stand', '7': 'Hit', '8': 'Hit','9': 'Hit','10': 'Hit','11': 'Hit'})
    r14 = pd.Series({'2': 'Stand', '3': 'Stand', '4': 'Stand', '5': 'Stand','6': 'Stand', '7': 'Stand', '8': 'Stand','9': 'Stand','10': 'Stand','11': 'Stand'})
    r15 = pd.Series({'2': 'Stand', '3': 'Stand', '4': 'Stand', '5': 'Stand','6': 'Stand', '7': 'Stand', '8': 'Stand','9': 'Stand','10': 'Stand','11': 'Stand'})
    r16 = pd.Series({'2': 'Stand', '3': 'Stand', '4': 'Stand', '5': 'Stand','6': 'Stand', '7': 'Stand', '8': 'Stand','9': 'Stand','10': 'Stand','11': 'Stand'})
    r17 = pd.Series({'2': 'Stand', '3': 'Stand', '4': 'Stand', '5': 'Stand','6': 'Stand', '7': 'Stand', '8': 'Stand','9': 'Stand','10': 'Stand','11': 'Stand'})
    r18 = pd.Series({'2': 'Stand', '3': 'Stand', '4': 'Stand', '5': 'Stand','6': 'Stand', '7': 'Stand', '8': 'Stand','9': 'Stand','10': 'Stand','11': 'Stand'})

    policy_df = pd.DataFrame([r1,r2,r3,r4,r5,r6,r7,r8,r9,r10,r11,r12,r13,r14,r15,r16,r17,r18], 
                    index=[4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21])
    
    return policy_df