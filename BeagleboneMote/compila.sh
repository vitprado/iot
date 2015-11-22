# Compila o código em C que lê os dados da SPI e grava no banco de dados
gcc -std=c99 postgresql.c -lm -lpq -o postgresql

