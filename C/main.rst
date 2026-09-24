                                      1 ;--------------------------------------------------------
                                      2 ; File Created by SDCC : free open source ANSI-C Compiler
                                      3 ; Version 4.2.0 #13081 (Linux)
                                      4 ;--------------------------------------------------------
                                      5 	.module main
                                      6 	.optsdcc -mstm8
                                      7 	
                                      8 ;--------------------------------------------------------
                                      9 ; Public variables in this module
                                     10 ;--------------------------------------------------------
                                     11 	.globl _main
                                     12 	.globl _alert_blink_fast
                                     13 	.globl _led_off
                                     14 	.globl _led_on
                                     15 	.globl _dht_read
                                     16 	.globl _dht_read_byte
                                     17 	.globl _dht_read_pin
                                     18 	.globl _dht_low
                                     19 	.globl _dht_high
                                     20 	.globl _dht_set_input
                                     21 	.globl _dht_set_output
                                     22 	.globl _delay_ms
                                     23 	.globl _delay_us
                                     24 ;--------------------------------------------------------
                                     25 ; ram data
                                     26 ;--------------------------------------------------------
                                     27 	.area DATA
                                     28 ;--------------------------------------------------------
                                     29 ; ram data
                                     30 ;--------------------------------------------------------
                                     31 	.area INITIALIZED
                                     32 ;--------------------------------------------------------
                                     33 ; Stack segment in internal ram
                                     34 ;--------------------------------------------------------
                                     35 	.area	SSEG
      000001                         36 __start__stack:
      000001                         37 	.ds	1
                                     38 
                                     39 ;--------------------------------------------------------
                                     40 ; absolute external ram data
                                     41 ;--------------------------------------------------------
                                     42 	.area DABS (ABS)
                                     43 
                                     44 ; default segment ordering for linker
                                     45 	.area HOME
                                     46 	.area GSINIT
                                     47 	.area GSFINAL
                                     48 	.area CONST
                                     49 	.area INITIALIZER
                                     50 	.area CODE
                                     51 
                                     52 ;--------------------------------------------------------
                                     53 ; interrupt vector
                                     54 ;--------------------------------------------------------
                                     55 	.area HOME
      008000                         56 __interrupt_vect:
      008000 82 00 80 07             57 	int s_GSINIT ; reset
                                     58 ;--------------------------------------------------------
                                     59 ; global & static initialisations
                                     60 ;--------------------------------------------------------
                                     61 	.area HOME
                                     62 	.area GSINIT
                                     63 	.area GSFINAL
                                     64 	.area GSINIT
      008007                         65 __sdcc_init_data:
                                     66 ; stm8_genXINIT() start
      008007 AE 00 00         [ 2]   67 	ldw x, #l_DATA
      00800A 27 07            [ 1]   68 	jreq	00002$
      00800C                         69 00001$:
      00800C 72 4F 00 00      [ 1]   70 	clr (s_DATA - 1, x)
      008010 5A               [ 2]   71 	decw x
      008011 26 F9            [ 1]   72 	jrne	00001$
      008013                         73 00002$:
      008013 AE 00 00         [ 2]   74 	ldw	x, #l_INITIALIZER
      008016 27 09            [ 1]   75 	jreq	00004$
      008018                         76 00003$:
      008018 D6 80 23         [ 1]   77 	ld	a, (s_INITIALIZER - 1, x)
      00801B D7 00 00         [ 1]   78 	ld	(s_INITIALIZED - 1, x), a
      00801E 5A               [ 2]   79 	decw	x
      00801F 26 F7            [ 1]   80 	jrne	00003$
      008021                         81 00004$:
                                     82 ; stm8_genXINIT() end
                                     83 	.area GSFINAL
      008021 CC 80 04         [ 2]   84 	jp	__sdcc_program_startup
                                     85 ;--------------------------------------------------------
                                     86 ; Home
                                     87 ;--------------------------------------------------------
                                     88 	.area HOME
                                     89 	.area HOME
      008004                         90 __sdcc_program_startup:
      008004 CC 81 51         [ 2]   91 	jp	_main
                                     92 ;	return from main will return to caller
                                     93 ;--------------------------------------------------------
                                     94 ; code
                                     95 ;--------------------------------------------------------
                                     96 	.area CODE
                                     97 ;	main.c: 12: void delay_us(uint16_t us) {
                                     98 ;	-----------------------------------------
                                     99 ;	 function delay_us
                                    100 ;	-----------------------------------------
      008024                        101 _delay_us:
                                    102 ;	main.c: 13: while (us--) { __asm__("nop"); __asm__("nop"); __asm__("nop"); }
      008024                        103 00101$:
      008024 90 93            [ 1]  104 	ldw	y, x
      008026 5A               [ 2]  105 	decw	x
      008027 90 5D            [ 2]  106 	tnzw	y
      008029 26 01            [ 1]  107 	jrne	00117$
      00802B 81               [ 4]  108 	ret
      00802C                        109 00117$:
      00802C 9D               [ 1]  110 	nop
      00802D 9D               [ 1]  111 	nop
      00802E 9D               [ 1]  112 	nop
      00802F 20 F3            [ 2]  113 	jra	00101$
                                    114 ;	main.c: 14: }
      008031 81               [ 4]  115 	ret
                                    116 ;	main.c: 15: void delay_ms(uint16_t ms) { while (ms--) delay_us(1000); }
                                    117 ;	-----------------------------------------
                                    118 ;	 function delay_ms
                                    119 ;	-----------------------------------------
      008032                        120 _delay_ms:
      008032                        121 00101$:
      008032 90 93            [ 1]  122 	ldw	y, x
      008034 5A               [ 2]  123 	decw	x
      008035 90 5D            [ 2]  124 	tnzw	y
      008037 26 01            [ 1]  125 	jrne	00117$
      008039 81               [ 4]  126 	ret
      00803A                        127 00117$:
      00803A 89               [ 2]  128 	pushw	x
      00803B AE 03 E8         [ 2]  129 	ldw	x, #0x03e8
      00803E CD 80 24         [ 4]  130 	call	_delay_us
      008041 85               [ 2]  131 	popw	x
      008042 20 EE            [ 2]  132 	jra	00101$
      008044 81               [ 4]  133 	ret
                                    134 ;	main.c: 17: void dht_set_output(void) { PD_DDR |= (1 << DHT_PIN); }
                                    135 ;	-----------------------------------------
                                    136 ;	 function dht_set_output
                                    137 ;	-----------------------------------------
      008045                        138 _dht_set_output:
      008045 72 14 50 11      [ 1]  139 	bset	0x5011, #2
      008049 81               [ 4]  140 	ret
                                    141 ;	main.c: 18: void dht_set_input(void)  { PD_DDR &= ~(1 << DHT_PIN); }
                                    142 ;	-----------------------------------------
                                    143 ;	 function dht_set_input
                                    144 ;	-----------------------------------------
      00804A                        145 _dht_set_input:
      00804A 72 15 50 11      [ 1]  146 	bres	0x5011, #2
      00804E 81               [ 4]  147 	ret
                                    148 ;	main.c: 19: void dht_high(void)       { PD_ODR |= (1 << DHT_PIN); }
                                    149 ;	-----------------------------------------
                                    150 ;	 function dht_high
                                    151 ;	-----------------------------------------
      00804F                        152 _dht_high:
      00804F 72 14 50 0F      [ 1]  153 	bset	0x500f, #2
      008053 81               [ 4]  154 	ret
                                    155 ;	main.c: 20: void dht_low(void)        { PD_ODR &= ~(1 << DHT_PIN); }
                                    156 ;	-----------------------------------------
                                    157 ;	 function dht_low
                                    158 ;	-----------------------------------------
      008054                        159 _dht_low:
      008054 72 15 50 0F      [ 1]  160 	bres	0x500f, #2
      008058 81               [ 4]  161 	ret
                                    162 ;	main.c: 21: uint8_t dht_read_pin(void){ return (PD_IDR & (1 << DHT_PIN)) ? 1 : 0; }
                                    163 ;	-----------------------------------------
                                    164 ;	 function dht_read_pin
                                    165 ;	-----------------------------------------
      008059                        166 _dht_read_pin:
      008059 72 05 50 10 03   [ 2]  167 	btjf	0x5010, #2, 00103$
      00805E 5F               [ 1]  168 	clrw	x
      00805F 5C               [ 1]  169 	incw	x
      008060 21                     170 	.byte 0x21
      008061                        171 00103$:
      008061 5F               [ 1]  172 	clrw	x
      008062                        173 00104$:
      008062 9F               [ 1]  174 	ld	a, xl
      008063 81               [ 4]  175 	ret
                                    176 ;	main.c: 23: uint8_t dht_read_byte(void) {
                                    177 ;	-----------------------------------------
                                    178 ;	 function dht_read_byte
                                    179 ;	-----------------------------------------
      008064                        180 _dht_read_byte:
      008064 52 02            [ 2]  181 	sub	sp, #2
                                    182 ;	main.c: 24: uint8_t byte = 0;
      008066 0F 01            [ 1]  183 	clr	(0x01, sp)
                                    184 ;	main.c: 25: for (uint8_t i = 0; i < 8; i++) {
      008068 0F 02            [ 1]  185 	clr	(0x02, sp)
      00806A                        186 00111$:
      00806A 7B 02            [ 1]  187 	ld	a, (0x02, sp)
      00806C A1 08            [ 1]  188 	cp	a, #0x08
      00806E 24 26            [ 1]  189 	jrnc	00109$
                                    190 ;	main.c: 26: while (!dht_read_pin());
      008070                        191 00101$:
      008070 CD 80 59         [ 4]  192 	call	_dht_read_pin
      008073 4D               [ 1]  193 	tnz	a
      008074 27 FA            [ 1]  194 	jreq	00101$
                                    195 ;	main.c: 27: delay_us(40);
      008076 AE 00 28         [ 2]  196 	ldw	x, #0x0028
      008079 CD 80 24         [ 4]  197 	call	_delay_us
                                    198 ;	main.c: 28: byte <<= 1;
      00807C 7B 01            [ 1]  199 	ld	a, (0x01, sp)
      00807E 48               [ 1]  200 	sll	a
      00807F 6B 01            [ 1]  201 	ld	(0x01, sp), a
                                    202 ;	main.c: 29: if (dht_read_pin()) byte |= 1;
      008081 CD 80 59         [ 4]  203 	call	_dht_read_pin
      008084 4D               [ 1]  204 	tnz	a
      008085 27 05            [ 1]  205 	jreq	00106$
      008087 04 01            [ 1]  206 	srl	(0x01, sp)
      008089 99               [ 1]  207 	scf
      00808A 09 01            [ 1]  208 	rlc	(0x01, sp)
                                    209 ;	main.c: 30: while (dht_read_pin());
      00808C                        210 00106$:
      00808C CD 80 59         [ 4]  211 	call	_dht_read_pin
      00808F 4D               [ 1]  212 	tnz	a
      008090 26 FA            [ 1]  213 	jrne	00106$
                                    214 ;	main.c: 25: for (uint8_t i = 0; i < 8; i++) {
      008092 0C 02            [ 1]  215 	inc	(0x02, sp)
      008094 20 D4            [ 2]  216 	jra	00111$
      008096                        217 00109$:
                                    218 ;	main.c: 32: return byte;
      008096 7B 01            [ 1]  219 	ld	a, (0x01, sp)
                                    220 ;	main.c: 33: }
      008098 5B 02            [ 2]  221 	addw	sp, #2
      00809A 81               [ 4]  222 	ret
                                    223 ;	main.c: 35: int8_t dht_read(uint8_t *humidity, uint8_t *temperature) {
                                    224 ;	-----------------------------------------
                                    225 ;	 function dht_read
                                    226 ;	-----------------------------------------
      00809B                        227 _dht_read:
      00809B 52 08            [ 2]  228 	sub	sp, #8
      00809D 1F 06            [ 2]  229 	ldw	(0x06, sp), x
                                    230 ;	main.c: 36: uint8_t data[5] = {0,0,0,0,0};
      00809F 0F 01            [ 1]  231 	clr	(0x01, sp)
      0080A1 0F 02            [ 1]  232 	clr	(0x02, sp)
      0080A3 0F 03            [ 1]  233 	clr	(0x03, sp)
      0080A5 0F 04            [ 1]  234 	clr	(0x04, sp)
      0080A7 0F 05            [ 1]  235 	clr	(0x05, sp)
                                    236 ;	main.c: 37: dht_set_output();
      0080A9 CD 80 45         [ 4]  237 	call	_dht_set_output
                                    238 ;	main.c: 38: dht_low();
      0080AC CD 80 54         [ 4]  239 	call	_dht_low
                                    240 ;	main.c: 39: delay_ms(18);
      0080AF AE 00 12         [ 2]  241 	ldw	x, #0x0012
      0080B2 CD 80 32         [ 4]  242 	call	_delay_ms
                                    243 ;	main.c: 40: dht_high();
      0080B5 CD 80 4F         [ 4]  244 	call	_dht_high
                                    245 ;	main.c: 41: delay_us(30);
      0080B8 AE 00 1E         [ 2]  246 	ldw	x, #0x001e
      0080BB CD 80 24         [ 4]  247 	call	_delay_us
                                    248 ;	main.c: 42: dht_set_input();
      0080BE CD 80 4A         [ 4]  249 	call	_dht_set_input
                                    250 ;	main.c: 43: delay_us(80);
      0080C1 AE 00 50         [ 2]  251 	ldw	x, #0x0050
      0080C4 CD 80 24         [ 4]  252 	call	_delay_us
                                    253 ;	main.c: 44: delay_us(80);
      0080C7 AE 00 50         [ 2]  254 	ldw	x, #0x0050
      0080CA CD 80 24         [ 4]  255 	call	_delay_us
                                    256 ;	main.c: 45: for (uint8_t i = 0; i < 5; i++) data[i] = dht_read_byte();
      0080CD 0F 08            [ 1]  257 	clr	(0x08, sp)
      0080CF                        258 00105$:
      0080CF 7B 08            [ 1]  259 	ld	a, (0x08, sp)
      0080D1 A1 05            [ 1]  260 	cp	a, #0x05
      0080D3 24 18            [ 1]  261 	jrnc	00101$
      0080D5 5F               [ 1]  262 	clrw	x
      0080D6 7B 08            [ 1]  263 	ld	a, (0x08, sp)
      0080D8 97               [ 1]  264 	ld	xl, a
      0080D9 89               [ 2]  265 	pushw	x
      0080DA 96               [ 1]  266 	ldw	x, sp
      0080DB 1C 00 03         [ 2]  267 	addw	x, #3
      0080DE 72 FB 01         [ 2]  268 	addw	x, (1, sp)
      0080E1 5B 02            [ 2]  269 	addw	sp, #2
      0080E3 89               [ 2]  270 	pushw	x
      0080E4 CD 80 64         [ 4]  271 	call	_dht_read_byte
      0080E7 85               [ 2]  272 	popw	x
      0080E8 F7               [ 1]  273 	ld	(x), a
      0080E9 0C 08            [ 1]  274 	inc	(0x08, sp)
      0080EB 20 E2            [ 2]  275 	jra	00105$
      0080ED                        276 00101$:
                                    277 ;	main.c: 46: dht_set_output();
      0080ED CD 80 45         [ 4]  278 	call	_dht_set_output
                                    279 ;	main.c: 47: dht_high();
      0080F0 CD 80 4F         [ 4]  280 	call	_dht_high
                                    281 ;	main.c: 48: if ((uint8_t)(data[0]+data[1]+data[2]+data[3]) != data[4]) return -1;
      0080F3 7B 01            [ 1]  282 	ld	a, (0x01, sp)
      0080F5 97               [ 1]  283 	ld	xl, a
      0080F6 7B 02            [ 1]  284 	ld	a, (0x02, sp)
      0080F8 89               [ 2]  285 	pushw	x
      0080F9 1B 02            [ 1]  286 	add	a, (2, sp)
      0080FB 85               [ 2]  287 	popw	x
      0080FC 95               [ 1]  288 	ld	xh, a
      0080FD 7B 03            [ 1]  289 	ld	a, (0x03, sp)
      0080FF 89               [ 2]  290 	pushw	x
      008100 1B 01            [ 1]  291 	add	a, (1, sp)
      008102 85               [ 2]  292 	popw	x
      008103 95               [ 1]  293 	ld	xh, a
      008104 7B 04            [ 1]  294 	ld	a, (0x04, sp)
      008106 89               [ 2]  295 	pushw	x
      008107 1B 01            [ 1]  296 	add	a, (1, sp)
      008109 85               [ 2]  297 	popw	x
      00810A 6B 08            [ 1]  298 	ld	(0x08, sp), a
      00810C 7B 05            [ 1]  299 	ld	a, (0x05, sp)
      00810E 11 08            [ 1]  300 	cp	a, (0x08, sp)
      008110 27 04            [ 1]  301 	jreq	00103$
      008112 A6 FF            [ 1]  302 	ld	a, #0xff
      008114 20 0B            [ 2]  303 	jra	00107$
      008116                        304 00103$:
                                    305 ;	main.c: 49: *humidity = data[0];
      008116 16 06            [ 2]  306 	ldw	y, (0x06, sp)
      008118 9F               [ 1]  307 	ld	a, xl
      008119 90 F7            [ 1]  308 	ld	(y), a
                                    309 ;	main.c: 50: *temperature = data[2];
      00811B 1E 0B            [ 2]  310 	ldw	x, (0x0b, sp)
      00811D 7B 03            [ 1]  311 	ld	a, (0x03, sp)
      00811F F7               [ 1]  312 	ld	(x), a
                                    313 ;	main.c: 51: return 0;
      008120 4F               [ 1]  314 	clr	a
      008121                        315 00107$:
                                    316 ;	main.c: 52: }
      008121 1E 09            [ 2]  317 	ldw	x, (9, sp)
      008123 5B 0C            [ 2]  318 	addw	sp, #12
      008125 FC               [ 2]  319 	jp	(x)
                                    320 ;	main.c: 54: void led_on(void)  { PD_ODR |= (1 << LED_PIN); }
                                    321 ;	-----------------------------------------
                                    322 ;	 function led_on
                                    323 ;	-----------------------------------------
      008126                        324 _led_on:
      008126 72 18 50 0F      [ 1]  325 	bset	0x500f, #4
      00812A 81               [ 4]  326 	ret
                                    327 ;	main.c: 55: void led_off(void) { PD_ODR &= ~(1 << LED_PIN); }
                                    328 ;	-----------------------------------------
                                    329 ;	 function led_off
                                    330 ;	-----------------------------------------
      00812B                        331 _led_off:
      00812B 72 19 50 0F      [ 1]  332 	bres	0x500f, #4
      00812F 81               [ 4]  333 	ret
                                    334 ;	main.c: 57: void alert_blink_fast(void) {
                                    335 ;	-----------------------------------------
                                    336 ;	 function alert_blink_fast
                                    337 ;	-----------------------------------------
      008130                        338 _alert_blink_fast:
      008130 88               [ 1]  339 	push	a
                                    340 ;	main.c: 58: for (uint8_t i = 0; i < 6; i++) {
      008131 0F 01            [ 1]  341 	clr	(0x01, sp)
      008133                        342 00103$:
      008133 7B 01            [ 1]  343 	ld	a, (0x01, sp)
      008135 A1 06            [ 1]  344 	cp	a, #0x06
      008137 24 16            [ 1]  345 	jrnc	00105$
                                    346 ;	main.c: 59: led_on(); delay_ms(100);
      008139 CD 81 26         [ 4]  347 	call	_led_on
      00813C AE 00 64         [ 2]  348 	ldw	x, #0x0064
      00813F CD 80 32         [ 4]  349 	call	_delay_ms
                                    350 ;	main.c: 60: led_off(); delay_ms(100);
      008142 CD 81 2B         [ 4]  351 	call	_led_off
      008145 AE 00 64         [ 2]  352 	ldw	x, #0x0064
      008148 CD 80 32         [ 4]  353 	call	_delay_ms
                                    354 ;	main.c: 58: for (uint8_t i = 0; i < 6; i++) {
      00814B 0C 01            [ 1]  355 	inc	(0x01, sp)
      00814D 20 E4            [ 2]  356 	jra	00103$
      00814F                        357 00105$:
                                    358 ;	main.c: 62: }
      00814F 84               [ 1]  359 	pop	a
      008150 81               [ 4]  360 	ret
                                    361 ;	main.c: 64: int main() {
                                    362 ;	-----------------------------------------
                                    363 ;	 function main
                                    364 ;	-----------------------------------------
      008151                        365 _main:
      008151 52 02            [ 2]  366 	sub	sp, #2
                                    367 ;	main.c: 67: CLK_CKDIVR = 0;
      008153 35 00 50 C6      [ 1]  368 	mov	0x50c6+0, #0x00
                                    369 ;	main.c: 68: PD_DDR |= (1 << LED_PIN);
      008157 72 18 50 11      [ 1]  370 	bset	0x5011, #4
                                    371 ;	main.c: 69: PD_CR1 |= (1 << LED_PIN);
      00815B C6 50 12         [ 1]  372 	ld	a, 0x5012
      00815E AA 10            [ 1]  373 	or	a, #0x10
      008160 C7 50 12         [ 1]  374 	ld	0x5012, a
                                    375 ;	main.c: 70: led_off();
      008163 CD 81 2B         [ 4]  376 	call	_led_off
                                    377 ;	main.c: 72: while (1) {
      008166                        378 00109$:
                                    379 ;	main.c: 73: delay_ms(2000);
      008166 AE 07 D0         [ 2]  380 	ldw	x, #0x07d0
      008169 CD 80 32         [ 4]  381 	call	_delay_ms
                                    382 ;	main.c: 75: if (dht_read(&humidity, &temperature) == 0) {
      00816C 96               [ 1]  383 	ldw	x, sp
      00816D 5C               [ 1]  384 	incw	x
      00816E 5C               [ 1]  385 	incw	x
      00816F 89               [ 2]  386 	pushw	x
      008170 96               [ 1]  387 	ldw	x, sp
      008171 1C 00 03         [ 2]  388 	addw	x, #3
      008174 CD 80 9B         [ 4]  389 	call	_dht_read
      008177 4D               [ 1]  390 	tnz	a
      008178 26 1F            [ 1]  391 	jrne	00106$
                                    392 ;	main.c: 76: if (temperature > 30 || humidity < 30) {
      00817A 7B 02            [ 1]  393 	ld	a, (0x02, sp)
      00817C A1 1E            [ 1]  394 	cp	a, #0x1e
      00817E 22 06            [ 1]  395 	jrugt	00101$
      008180 7B 01            [ 1]  396 	ld	a, (0x01, sp)
      008182 A1 1E            [ 1]  397 	cp	a, #0x1e
      008184 24 05            [ 1]  398 	jrnc	00102$
      008186                        399 00101$:
                                    400 ;	main.c: 77: alert_blink_fast();   // bad condition — fast blink
      008186 CD 81 30         [ 4]  401 	call	_alert_blink_fast
      008189 20 DB            [ 2]  402 	jra	00109$
      00818B                        403 00102$:
                                    404 ;	main.c: 79: led_on(); delay_ms(50); led_off();  // OK — quick heartbeat blink
      00818B CD 81 26         [ 4]  405 	call	_led_on
      00818E AE 00 32         [ 2]  406 	ldw	x, #0x0032
      008191 CD 80 32         [ 4]  407 	call	_delay_ms
      008194 CD 81 2B         [ 4]  408 	call	_led_off
      008197 20 CD            [ 2]  409 	jra	00109$
      008199                        410 00106$:
                                    411 ;	main.c: 83: led_on(); delay_ms(50); led_off(); delay_ms(50);
      008199 CD 81 26         [ 4]  412 	call	_led_on
      00819C AE 00 32         [ 2]  413 	ldw	x, #0x0032
      00819F CD 80 32         [ 4]  414 	call	_delay_ms
      0081A2 CD 81 2B         [ 4]  415 	call	_led_off
      0081A5 AE 00 32         [ 2]  416 	ldw	x, #0x0032
      0081A8 CD 80 32         [ 4]  417 	call	_delay_ms
                                    418 ;	main.c: 84: led_on(); delay_ms(50); led_off();
      0081AB CD 81 26         [ 4]  419 	call	_led_on
      0081AE AE 00 32         [ 2]  420 	ldw	x, #0x0032
      0081B1 CD 80 32         [ 4]  421 	call	_delay_ms
      0081B4 CD 81 2B         [ 4]  422 	call	_led_off
      0081B7 20 AD            [ 2]  423 	jra	00109$
                                    424 ;	main.c: 87: }
      0081B9 5B 02            [ 2]  425 	addw	sp, #2
      0081BB 81               [ 4]  426 	ret
                                    427 	.area CODE
                                    428 	.area CONST
                                    429 	.area INITIALIZER
                                    430 	.area CABS (ABS)
