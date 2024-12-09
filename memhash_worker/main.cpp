#include <iostream>
#include "Server.h"

int main() {
    try {
        Server relay(9100);
    }
    catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
    }

    return 0;
}
