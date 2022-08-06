



def get_yahoo_csv(code='000001'):
    data_path = Path(os.getcwd()) / 'datas/000001.SZ.csv'
    date_frame = pd.read_csv(data_path)
    date_frame['datetime'] = pd.to_datetime(date_frame['Date'])  #
    date_frame.set_index('datetime', inplace=True)  #
    date_frame['openinterest'] = 0

    return date_frame

def write_csv_to_compare_datas(first, second):
    first.to_csv('000001.first.day.csv', index=True)
    second.to_csv('000001.second.day.csv', index=True)