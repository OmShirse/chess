;--------------------------------------------------------
; File Created by SDCC : free open source ANSI-C Compiler
; Version 4.2.0 #13081 (Linux)
;--------------------------------------------------------
	.module main
	.optsdcc -mstm8
	
;--------------------------------------------------------
; Public variables in this module
;--------------------------------------------------------
	.globl _main
	.globl _alert_blink_fast
	.globl _led_off
	.globl _led_on
	.globl _dht_read
	.globl _dht_read_byte
	.globl _dht_read_pin
	.globl _dht_low
	.globl _dht_high
	.globl _dht_set_input
	.globl _dht_set_output
	.globl _delay_ms
	.globl _delay_us
;--------------------------------------------------------
; ram data
;--------------------------------------------------------
	.area DATA
;--------------------------------------------------------
; ram data
;--------------------------------------------------------
	.area INITIALIZED
;--------------------------------------------------------
; Stack segment in internal ram
;--------------------------------------------------------
	.area	SSEG
__start__stack:
	.ds	1

;--------------------------------------------------------
; absolute external ram data
;--------------------------------------------------------
	.area DABS (ABS)

; default segment ordering for linker
	.area HOME
	.area GSINIT
	.area GSFINAL
	.area CONST
	.area INITIALIZER
	.area CODE

;--------------------------------------------------------
; interrupt vector
;--------------------------------------------------------
	.area HOME
__interrupt_vect:
	int s_GSINIT ; reset
;--------------------------------------------------------
; global & static initialisations
;--------------------------------------------------------
	.area HOME
	.area GSINIT
	.area GSFINAL
	.area GSINIT
__sdcc_init_data:
; stm8_genXINIT() start
	ldw x, #l_DATA
	jreq	00002$
00001$:
	clr (s_DATA - 1, x)
	decw x
	jrne	00001$
00002$:
	ldw	x, #l_INITIALIZER
	jreq	00004$
00003$:
	ld	a, (s_INITIALIZER - 1, x)
	ld	(s_INITIALIZED - 1, x), a
	decw	x
	jrne	00003$
00004$:
; stm8_genXINIT() end
	.area GSFINAL
	jp	__sdcc_program_startup
;--------------------------------------------------------
; Home
;--------------------------------------------------------
	.area HOME
	.area HOME
__sdcc_program_startup:
	jp	_main
;	return from main will return to caller
;--------------------------------------------------------
; code
;--------------------------------------------------------
	.area CODE
;	main.c: 12: void delay_us(uint16_t us) {
;	-----------------------------------------
;	 function delay_us
;	-----------------------------------------
_delay_us:
;	main.c: 13: while (us--) { __asm__("nop"); __asm__("nop"); __asm__("nop"); }
00101$:
	ldw	y, x
	decw	x
	tnzw	y
	jrne	00117$
	ret
00117$:
	nop
	nop
	nop
	jra	00101$
;	main.c: 14: }
	ret
;	main.c: 15: void delay_ms(uint16_t ms) { while (ms--) delay_us(1000); }
;	-----------------------------------------
;	 function delay_ms
;	-----------------------------------------
_delay_ms:
00101$:
	ldw	y, x
	decw	x
	tnzw	y
	jrne	00117$
	ret
00117$:
	pushw	x
	ldw	x, #0x03e8
	call	_delay_us
	popw	x
	jra	00101$
	ret
;	main.c: 17: void dht_set_output(void) { PD_DDR |= (1 << DHT_PIN); }
;	-----------------------------------------
;	 function dht_set_output
;	-----------------------------------------
_dht_set_output:
	bset	0x5011, #2
	ret
;	main.c: 18: void dht_set_input(void)  { PD_DDR &= ~(1 << DHT_PIN); }
;	-----------------------------------------
;	 function dht_set_input
;	-----------------------------------------
_dht_set_input:
	bres	0x5011, #2
	ret
;	main.c: 19: void dht_high(void)       { PD_ODR |= (1 << DHT_PIN); }
;	-----------------------------------------
;	 function dht_high
;	-----------------------------------------
_dht_high:
	bset	0x500f, #2
	ret
;	main.c: 20: void dht_low(void)        { PD_ODR &= ~(1 << DHT_PIN); }
;	-----------------------------------------
;	 function dht_low
;	-----------------------------------------
_dht_low:
	bres	0x500f, #2
	ret
;	main.c: 21: uint8_t dht_read_pin(void){ return (PD_IDR & (1 << DHT_PIN)) ? 1 : 0; }
;	-----------------------------------------
;	 function dht_read_pin
;	-----------------------------------------
_dht_read_pin:
	btjf	0x5010, #2, 00103$
	clrw	x
	incw	x
	.byte 0x21
00103$:
	clrw	x
00104$:
	ld	a, xl
	ret
;	main.c: 23: uint8_t dht_read_byte(void) {
;	-----------------------------------------
;	 function dht_read_byte
;	-----------------------------------------
_dht_read_byte:
	sub	sp, #2
;	main.c: 24: uint8_t byte = 0;
	clr	(0x01, sp)
;	main.c: 25: for (uint8_t i = 0; i < 8; i++) {
	clr	(0x02, sp)
00111$:
	ld	a, (0x02, sp)
	cp	a, #0x08
	jrnc	00109$
;	main.c: 26: while (!dht_read_pin());
00101$:
	call	_dht_read_pin
	tnz	a
	jreq	00101$
;	main.c: 27: delay_us(40);
	ldw	x, #0x0028
	call	_delay_us
;	main.c: 28: byte <<= 1;
	ld	a, (0x01, sp)
	sll	a
	ld	(0x01, sp), a
;	main.c: 29: if (dht_read_pin()) byte |= 1;
	call	_dht_read_pin
	tnz	a
	jreq	00106$
	srl	(0x01, sp)
	scf
	rlc	(0x01, sp)
;	main.c: 30: while (dht_read_pin());
00106$:
	call	_dht_read_pin
	tnz	a
	jrne	00106$
;	main.c: 25: for (uint8_t i = 0; i < 8; i++) {
	inc	(0x02, sp)
	jra	00111$
00109$:
;	main.c: 32: return byte;
	ld	a, (0x01, sp)
;	main.c: 33: }
	addw	sp, #2
	ret
;	main.c: 35: int8_t dht_read(uint8_t *humidity, uint8_t *temperature) {
;	-----------------------------------------
;	 function dht_read
;	-----------------------------------------
_dht_read:
	sub	sp, #8
	ldw	(0x06, sp), x
;	main.c: 36: uint8_t data[5] = {0,0,0,0,0};
	clr	(0x01, sp)
	clr	(0x02, sp)
	clr	(0x03, sp)
	clr	(0x04, sp)
	clr	(0x05, sp)
;	main.c: 37: dht_set_output();
	call	_dht_set_output
;	main.c: 38: dht_low();
	call	_dht_low
;	main.c: 39: delay_ms(18);
	ldw	x, #0x0012
	call	_delay_ms
;	main.c: 40: dht_high();
	call	_dht_high
;	main.c: 41: delay_us(30);
	ldw	x, #0x001e
	call	_delay_us
;	main.c: 42: dht_set_input();
	call	_dht_set_input
;	main.c: 43: delay_us(80);
	ldw	x, #0x0050
	call	_delay_us
;	main.c: 44: delay_us(80);
	ldw	x, #0x0050
	call	_delay_us
;	main.c: 45: for (uint8_t i = 0; i < 5; i++) data[i] = dht_read_byte();
	clr	(0x08, sp)
00105$:
	ld	a, (0x08, sp)
	cp	a, #0x05
	jrnc	00101$
	clrw	x
	ld	a, (0x08, sp)
	ld	xl, a
	pushw	x
	ldw	x, sp
	addw	x, #3
	addw	x, (1, sp)
	addw	sp, #2
	pushw	x
	call	_dht_read_byte
	popw	x
	ld	(x), a
	inc	(0x08, sp)
	jra	00105$
00101$:
;	main.c: 46: dht_set_output();
	call	_dht_set_output
;	main.c: 47: dht_high();
	call	_dht_high
;	main.c: 48: if ((uint8_t)(data[0]+data[1]+data[2]+data[3]) != data[4]) return -1;
	ld	a, (0x01, sp)
	ld	xl, a
	ld	a, (0x02, sp)
	pushw	x
	add	a, (2, sp)
	popw	x
	ld	xh, a
	ld	a, (0x03, sp)
	pushw	x
	add	a, (1, sp)
	popw	x
	ld	xh, a
	ld	a, (0x04, sp)
	pushw	x
	add	a, (1, sp)
	popw	x
	ld	(0x08, sp), a
	ld	a, (0x05, sp)
	cp	a, (0x08, sp)
	jreq	00103$
	ld	a, #0xff
	jra	00107$
00103$:
;	main.c: 49: *humidity = data[0];
	ldw	y, (0x06, sp)
	ld	a, xl
	ld	(y), a
;	main.c: 50: *temperature = data[2];
	ldw	x, (0x0b, sp)
	ld	a, (0x03, sp)
	ld	(x), a
;	main.c: 51: return 0;
	clr	a
00107$:
;	main.c: 52: }
	ldw	x, (9, sp)
	addw	sp, #12
	jp	(x)
;	main.c: 54: void led_on(void)  { PD_ODR |= (1 << LED_PIN); }
;	-----------------------------------------
;	 function led_on
;	-----------------------------------------
_led_on:
	bset	0x500f, #4
	ret
;	main.c: 55: void led_off(void) { PD_ODR &= ~(1 << LED_PIN); }
;	-----------------------------------------
;	 function led_off
;	-----------------------------------------
_led_off:
	bres	0x500f, #4
	ret
;	main.c: 57: void alert_blink_fast(void) {
;	-----------------------------------------
;	 function alert_blink_fast
;	-----------------------------------------
_alert_blink_fast:
	push	a
;	main.c: 58: for (uint8_t i = 0; i < 6; i++) {
	clr	(0x01, sp)
00103$:
	ld	a, (0x01, sp)
	cp	a, #0x06
	jrnc	00105$
;	main.c: 59: led_on(); delay_ms(100);
	call	_led_on
	ldw	x, #0x0064
	call	_delay_ms
;	main.c: 60: led_off(); delay_ms(100);
	call	_led_off
	ldw	x, #0x0064
	call	_delay_ms
;	main.c: 58: for (uint8_t i = 0; i < 6; i++) {
	inc	(0x01, sp)
	jra	00103$
00105$:
;	main.c: 62: }
	pop	a
	ret
;	main.c: 64: int main() {
;	-----------------------------------------
;	 function main
;	-----------------------------------------
_main:
	sub	sp, #2
;	main.c: 67: CLK_CKDIVR = 0;
	mov	0x50c6+0, #0x00
;	main.c: 68: PD_DDR |= (1 << LED_PIN);
	bset	0x5011, #4
;	main.c: 69: PD_CR1 |= (1 << LED_PIN);
	ld	a, 0x5012
	or	a, #0x10
	ld	0x5012, a
;	main.c: 70: led_off();
	call	_led_off
;	main.c: 72: while (1) {
00109$:
;	main.c: 73: delay_ms(2000);
	ldw	x, #0x07d0
	call	_delay_ms
;	main.c: 75: if (dht_read(&humidity, &temperature) == 0) {
	ldw	x, sp
	incw	x
	incw	x
	pushw	x
	ldw	x, sp
	addw	x, #3
	call	_dht_read
	tnz	a
	jrne	00106$
;	main.c: 76: if (temperature > 30 || humidity < 30) {
	ld	a, (0x02, sp)
	cp	a, #0x1e
	jrugt	00101$
	ld	a, (0x01, sp)
	cp	a, #0x1e
	jrnc	00102$
00101$:
;	main.c: 77: alert_blink_fast();   // bad condition — fast blink
	call	_alert_blink_fast
	jra	00109$
00102$:
;	main.c: 79: led_on(); delay_ms(50); led_off();  // OK — quick heartbeat blink
	call	_led_on
	ldw	x, #0x0032
	call	_delay_ms
	call	_led_off
	jra	00109$
00106$:
;	main.c: 83: led_on(); delay_ms(50); led_off(); delay_ms(50);
	call	_led_on
	ldw	x, #0x0032
	call	_delay_ms
	call	_led_off
	ldw	x, #0x0032
	call	_delay_ms
;	main.c: 84: led_on(); delay_ms(50); led_off();
	call	_led_on
	ldw	x, #0x0032
	call	_delay_ms
	call	_led_off
	jra	00109$
;	main.c: 87: }
	addw	sp, #2
	ret
	.area CODE
	.area CONST
	.area INITIALIZER
	.area CABS (ABS)
