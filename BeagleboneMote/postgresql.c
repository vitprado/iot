/*
* SPI testing utility (using spidev driver)
*
* Copyright (c) 2007  MontaVista Software, Inc.
* Copyright (c) 2007  Anton Vorontsov
*
* This program is free software; you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation; either version 2 of the License.
*
* Cross-compile with cross-gcc -I/path/to/cross-kernel/include
*
* gcc postgresql.c -lpq -o postgresql
*
*/

#include <stdint.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <getopt.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/types.h>
#include <linux/spi/spidev.h>

// Comunicação com o banco de dados
#include "/usr/include/postgresql/libpq-fe.h"

#define ARRAY_SIZE(a) (sizeof(a) / sizeof((a)[0]))

static void pabort(const char *s) {
    perror(s);
	abort();
}

// Abort do banco de dados
static void exit_nicely(PGconn *conn)
{
	PQfinish(conn);
	exit(1);
}

static const char *device = "/dev/spidev1.0";
static uint8_t mode = 3;
static uint8_t bits = 8;
static uint32_t speed = 2000000;
static uint16_t delay;
int fd;

uint8_t tx[] = {
	0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
};
uint8_t rx[] = {
	0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
};


// SONOMA Register Locations
#define SONOMA_ADDR_CMD        0x00	// [int ] Command Register (see Command Register section)
#define SONOMA_ADDR_FWDATE     0x01	// [int ] Firmware release date in hex format (0x00YMDD)
#define SONOMA_ADDR_SAMPLES    0x08	// [int ] High-Rate Samples per Low Rate (default 400)
#define SONOMA_S0_GAIN         0x0D	// [S.21] Input S0 Gain Calibration. Positive values only
#define SONOMA_S2_GAIN         0x0F	// [S.21] Input S2 Gain Calibration. Positive values only
#define SONOMA_ADDR_VA_FUND	   0x2D	// [S.23] Fundamental Voltage for VA source
#define SONOMA_ADDR_VA_HARM    0x2F	// [S.23] Harmonic Voltage for VA source
#define SONOMA_ADDR_VA         0x33	// [S.23] Instantaneous Voltage for VA source
#define SONOMA_ADDR_UART_BAUD  0xB1	// [int ] Baud rate for UART interface (Default 38400)

#define SONOMA_ADDR_VA_RMS	   0x2B	// [S.23] RMS Voltage for VA source
#define SONOMA_ADDR_IA_RMS	   0x3E	// [S.23] RMS Current for IA source
#define SONOMA_ADDR_WATT_A	   0x4B	// [S.23] Active Power for VA source

// Ajuste para os valores recebidos pela SONOMA
#define SONOMA_TRIMER_VA_RMS	   0.0015	// [S.23]
#define SONOMA_TRIMER_IA_RMS	   0.0015	// [S.23] (NÃO CONFERIDO)
#define SONOMA_TRIMER_WATT_A	   0.0015	// [S.23] (NÃO CONFERIDO)

volatile uint32_t param[10];

float CalculaS21(uint8_t *rx){

	float retorno = 0;

	retorno += rx[0] & 64 ? 2 : 0; // bit da posição 22
	retorno += rx[0] & 32 ? 1 : 0; // bit da posição 21
	retorno += rx[0] & 16 ? 0.5 : 0; // 1/2
	retorno += rx[0] & 8  ? 0.25 : 0; // 1/4
	retorno += rx[0] & 4  ? 0.125 : 0; // 1/8
	retorno += rx[0] & 2  ? 0.0625 : 0; // 1/16
	retorno += rx[0] & 1  ? 0.03125 : 0; // 1/32

	retorno += rx[1] & 128 ? 0.015625 : 0; // 1/64
	retorno += rx[1] & 64  ? 0.0078125 : 0; // 1/128
	retorno += rx[1] & 32  ? 0.00390625 : 0; // 1/256
	retorno += rx[1] & 16  ? 0.001953125 : 0; // 1/512
	retorno += rx[1] & 8   ? 0.0009765625 : 0; // 1/1024
	retorno += rx[1] & 4   ? 0.00048828125 : 0; // 1/2048
	retorno += rx[1] & 2   ? 0.000244140625 : 0; // 1/4096
	retorno += rx[1] & 1   ? 0.0001220703125 : 0; // 1/8192

	retorno += rx[2] & 128 ? 0.00006103515625 : 0; // 1/16384
	retorno += rx[2] & 64  ? 0.00003051757813 : 0; // 1/32768
	retorno += rx[2] & 32  ? 0.00001525878906 : 0; // 1/65536
	retorno += rx[2] & 16  ? 0.000007629394531 : 0; // 1/131072
	retorno += rx[2] & 8   ? 0.000003814697266 : 0; // 1/262144
	retorno += rx[2] & 4   ? 0.000001907348633 : 0; // 1/524288
	retorno += rx[2] & 2   ? 0.0000009536743164 : 0; // 1/1048576
	retorno += rx[2] & 1   ? 0.0000004768371582 : 0; // 1/2097152

	retorno = rx[0] & 128 ? (-1) * retorno : retorno; // Verifica o sinal

	return retorno;
}

float CalculaS23(uint8_t *rx){

	float retorno = 0;

	retorno += rx[0] & 64 ? 0.5 : 0; // 1/2
	retorno += rx[0] & 32 ? 0.25 : 0; // 1/4
	retorno += rx[0] & 16 ? 0.125 : 0; // 1/8
	retorno += rx[0] & 8  ? 0.0625 : 0; // 1/16
	retorno += rx[0] & 4  ? 0.03125 : 0; // 1/32
	retorno += rx[0] & 2  ? 0.015625 : 0; // 1/64
	retorno += rx[0] & 1  ? 0.0078125 : 0; // 1/128

	retorno += rx[1] & 128 ? 0.00390625 : 0; // 1/256
	retorno += rx[1] & 64  ? 0.001953125 : 0; // 1/512
	retorno += rx[1] & 32  ? 0.0009765625 : 0; // 1/1024
	retorno += rx[1] & 16  ? 0.00048828125 : 0; // 1/2048
	retorno += rx[1] & 8   ? 0.000244140625 : 0; // 1/4096
	retorno += rx[1] & 4   ? 0.0001220703125 : 0; // 1/8192
	retorno += rx[1] & 2   ? 0.00006103515625 : 0; // 1/16384
	retorno += rx[1] & 1   ? 0.00003051757813 : 0; // 1/32768

	retorno += rx[2] & 128 ? 0.00001525878906 : 0; // 1/65536
	retorno += rx[2] & 64  ? 0.000007629394531 : 0; // 1/131072
	retorno += rx[2] & 32  ? 0.000003814697266 : 0; // 1/262144
	retorno += rx[2] & 16  ? 0.000001907348633 : 0; // 1/524288
	retorno += rx[2] & 8   ? 0.0000009536743164 : 0; // 1/1048576
	retorno += rx[2] & 4   ? 0.0000004768371582 : 0; // 1/2097152
	retorno += rx[2] & 2   ? 0.0000002384185791 : 0; // 1/4194304
	retorno += rx[2] & 1   ? 0.0000001192092896 : 0; // 1/8388608

	retorno = rx[0] & 128 ? (-1) * retorno : retorno; // Verifica o sinal

	return retorno;
}

uint32_t CalculaInt(){

	uint32_t retorno;

	retorno = rx[4] + (rx[3] << 8) + (rx[2] << 16);

	return retorno;
}

static void transfer() {
	int ret;

	struct spi_ioc_transfer tr = { .tx_buf = (unsigned long) tx, .rx_buf =
		(unsigned long) rx, .len = ARRAY_SIZE(tx), .delay_usecs = delay,
		.speed_hz = 0, .bits_per_word = 0, };

		ret = ioctl(fd, SPI_IOC_MESSAGE(1), &tr);
		if (ret == 1)
			pabort("can't send spi message");

		for (ret = 0; ret < ARRAY_SIZE(tx); ret++) {
			printf("0x%.2X ", rx[ret]);
		}
		puts("");
	}

/**
* \brief       Reads the value of a register
* \par         Details
*
* \param[in]   uchRegAddr      - Register Address
*
* \retval      Register Value
*/
static void spiRead(uint8_t uchRegAddr) {

	//preparing read command
	tx[0] = uchRegAddr >> 6;
	tx[0] = (tx[0] << 2) + 1;
	tx[1] = 0x3F & uchRegAddr;
	tx[1] = tx[1] << 2;
	tx[2] = 0;
	tx[3] = 0;
	tx[4] = 0;
	tx[5] = 0;

	transfer();

}

void spiWrite(uint8_t uchRegAddr, uint32_t unRegValue) {

	//preparing write command
	tx[0] = uchRegAddr >> 6;
	tx[0] = (tx[0] << 2) + 1;
	tx[1] = 0x3F & uchRegAddr;
	tx[1] = (tx[1] << 2) + 2;
	tx[2] = unRegValue >> 16;
	tx[3] = unRegValue >> 8;
	tx[4] = unRegValue;
	tx[5] = 0;

	transfer();

}

void print_usage(const char *prog) {
	printf("Usage: %s [-DsbdlHOLC3]\n", prog);
	puts("  -D --device   device to use (default /dev/spidev1.1)\n"
		"  -s --speed    max speed (Hz)\n"
		"  -d --delay    delay (usec)\n"
		"  -b --bpw      bits per word \n"
		"  -l --loop     loopback\n"
		"  -H --cpha     clock phase\n"
		"  -O --cpol     clock polarity\n"
		"  -L --lsb      least significant bit first\n"
		"  -C --cs-high  chip select active high\n"
		"  -3 --3wire    SI/SO signals shared\n");
	exit(1);
}

void parse_opts(int argc, char *argv[]) {
	while (1) {
		static const struct option lopts[] = { { "device", 1, 0, 'D' }, {
			"speed", 1, 0, 's' }, { "delay", 1, 0, 'd' },
			{ "bpw", 1, 0, 'b' }, { "loop", 0, 0, 'l' },
			{ "cpha", 0, 0, 'H' }, { "cpol", 0, 0, 'O' },
			{ "lsb", 0, 0, 'L' }, { "cs-high", 0, 0, 'C' }, { "3wire", 0, 0,
			'3' }, { NULL, 0, 0, 0 }, };
			int c;

			c = getopt_long(argc, argv, "D:s:d:b:lHOLC3", lopts, NULL);

			if (c == -1)
				break;

			switch (c) {
				case 'D':
				device = optarg;
				break;
				case 's':
				speed = atoi(optarg);
				break;
				case 'd':
				delay = atoi(optarg);
				break;
				case 'b':
				bits = atoi(optarg);
				break;
				case 'l':
				mode |= SPI_LOOP;
				break;
				case 'H':
				mode |= SPI_CPHA;
				break;
				case 'O':
				mode |= SPI_CPOL;
				break;
				case 'L':
				mode |= SPI_LSB_FIRST;
				break;
				case 'C':
				mode |= SPI_CS_HIGH;
				break;
				case '3':
				mode |= SPI_3WIRE;
				break;
				default:
				print_usage(argv[0]);
				break;
			}
		}
	}

int main(int argc, char *argv[]) {

	char query [200];

	float valor1 = 0;
	float valor2 = 0;
	float valor3 = 0;
	float valor4 = 0;
	float valor5 = 0;
	float valor6 = 0;

	// Parametros de configuração da comunicação com o banco de dados
	const char *conninfo;
	PGconn     *conn;
	PGresult   *res;
	int         nFields;
	int         i,
	j;

	// Estabelece a comunicação com o banco.
	if (argc > 2)
		conninfo = argv[2];
	else {
		conninfo = "dbname = iot";
		conninfo = "user = postgres";
	}

	// Make a connection to the database
	conn = PQconnectdb(conninfo);

	int ret = 0;

	parse_opts(argc, argv);

	fd = open(device, O_RDWR);
	if (fd < 0)
		pabort("can't open device");

	//spi mode
	 ret = ioctl(fd, SPI_IOC_WR_MODE, &mode);
	 if (ret == -1)
	 	pabort("can't set spi mode");

	 ret = ioctl(fd, SPI_IOC_RD_MODE, &mode);
	 if (ret == -1)
	 	pabort("can't get spi mode");


	// bits per word
	ret = ioctl(fd, SPI_IOC_WR_BITS_PER_WORD, &bits);
	if (ret == -1)
		pabort("can't set bits per word");

	ret = ioctl(fd, SPI_IOC_RD_BITS_PER_WORD, &bits);
	if (ret == -1)
		pabort("can't get bits per word");

	// max speed hz
	ret = ioctl(fd, SPI_IOC_WR_MAX_SPEED_HZ, &speed);
	if (ret == -1)
 		pabort("can't set max speed hz");

	ret = ioctl(fd, SPI_IOC_RD_MAX_SPEED_HZ, &speed);
	if (ret == -1)
 		pabort("can't get max speed hz");

	printf("spi mode: %d\n", mode);
	printf("bits per word: %d\n", bits);
	printf("max speed: %d Hz (%d KHz)\n", speed, speed / 1000);


	printf("---------- Iniciando leitura ----------\n");
	// Rotina de captura e persistencia de dados
 	while(1){

	 	// Leitura de VA_RMS
	 	sleep(0.1);
	 	spiRead(SONOMA_ADDR_VA_RMS);
	 	valor1 = CalculaS23(&rx[2]) / SONOMA_TRIMER_VA_RMS;

	 	// Leitura de IA_RMS
	 	sleep(0.1);
	 	spiRead(SONOMA_ADDR_IA_RMS);
	 	valor2 = CalculaS23(&rx[2]);// / SONOMA_TRIMER_IA_RMS;

	 	// Leitura de WATT_A
	 	sleep(0.1);
	 	spiRead(SONOMA_ADDR_WATT_A);
	 	valor3 = CalculaS23(&rx[2]);// / SONOMA_TRIMER_WATT_A;

		// Check to see that the backend connection was successfully made
	 	if (PQstatus(conn) != CONNECTION_OK)
	 	{
	 		fprintf(stderr, "Connection to database failed: %s",
	 			PQerrorMessage(conn));
	 		exit_nicely(conn);
	 	}

	 	sprintf (query, "INSERT INTO medicao VALUES (DEFAULT, '%.6f','%.6f','%.6f','%.6f','%.6f','%.6f');\n", valor1, valor2, valor3, valor4, valor5, valor6);
		printf ("%s\n",query);

	 	res = PQexec(conn, query);
	 	if (PQresultStatus(res) != PGRES_COMMAND_OK)
	 	{
	 		fprintf(stderr, "BEGIN command failed: %s", PQerrorMessage(conn));
	 		PQclear(res);
	 		exit_nicely(conn);
	 	}

	 	sleep(0.5);
	}
	// Final da rotina de captura e persistencia de dados

	// Fecha a conexao com o banco de dados
	PQfinish(conn);

	// Fecha a conexao SPI
	close(fd);

	return ret;
}
