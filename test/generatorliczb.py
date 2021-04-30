from datetime import timedelta, date, datetime

out = ""

def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)

start_date = date(2024, 1, 1)
end_date = date(2025, 1, 1)
for single_date in daterange(start_date, end_date):
    out += single_date.strftime("%d.%m") + " " + str(((single_date.timetuple().tm_yday + 1) ** 20))[:6]  + " | "

with open(r"kalendarz.txt", "w") as f:
    f.write(out)

print(out)