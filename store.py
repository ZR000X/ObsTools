def journal_days(year: str, month: str, day_start: int, day_end: int) -> str:
    output:str = ""
    for i in range(day_start,day_end):
        if i < 10:
           output+="- [["+year+"-"+month+"-0"+str(i)+"]]\n" 
        else:
            output+="- [["+year+"-"+month+"-"+str(i)+"]]\n"
    if i < 10:
           output+="- [["+year+"-"+month+"-0"+str(day_end)+"]]"
    else:
        output+="- [["+year+"-"+month+"-"+str(day_end)+"]]"
    return output

print(journal_days("2022","01",12,31))