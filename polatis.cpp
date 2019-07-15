#include <iostream>
#include <string>
using namespace std;

int main(int argc, char** argv)
{
    string file_path = argv[0];
    size_t name_start_index = file_path.find_last_of("/\\") + 1;
    string drivers_folder = file_path.substr(0, name_start_index);
    if (drivers_folder.empty())
    {
        drivers_folder = "\.\\";
    }
    string server_folder = drivers_folder + "..";
    string driver_name = file_path.substr(name_start_index, file_path.find_last_of(".")-name_start_index);
    string driver_log_path = "\"" + server_folder + "\\Logs" + "\"";
    string driver_env = drivers_folder+"cloudshell-L1-" + driver_name;
    string driver_main = "\"" + driver_env + "\\main.py" + "\"";
    string driver_interpriter = "\""+driver_env + "\\Scripts\\python.exe"+"\"";
    
    string port;
    if(argc > 1)
    {
        port = argv[1];
    } else {
        port = "4000";
    }
    
    string command = "\"" + driver_interpriter + " " + driver_main + " " + port + " " + driver_log_path + "\"";
    cout << "Starting driver " + driver_name << "\n"; 
    cout << command << "\n";
    system(command.c_str());
    return 0;
}