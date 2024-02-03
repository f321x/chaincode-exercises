CC := c++
CFLAGS := -Wall -Wextra -Werror -g3 -std=c++98
NAME :=	mempool
INCLUDES := -I./includes
SRCS := src/main.cpp src/MempoolTransaction.cpp

OBJS := $(SRCS:.cpp=.o)
all: $(NAME)

%.o: %.cpp
	$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

$(NAME): $(OBJS)
	$(CC) $(CFLAGS) $(INCLUDES) $(OBJS) -o $(NAME)

clean:
	rm -f $(OBJS)

fclean: clean
	rm -f $(NAME)

re: fclean all

.PHONY: clean fclean all re
