#include "pose.h"

namespace {
#define DIM 18
#define EDIM 18
#define MEDIM 18
typedef void (*Hfun)(double *, double *, double *);
const static double MAHA_THRESH_4 = 7.814727903251177;
const static double MAHA_THRESH_10 = 7.814727903251177;
const static double MAHA_THRESH_13 = 7.814727903251177;
const static double MAHA_THRESH_14 = 7.814727903251177;

/******************************************************************************
 *                      Code generated with SymPy 1.14.0                      *
 *                                                                            *
 *              See http://www.sympy.org/ for more information.               *
 *                                                                            *
 *                         This file is part of 'ekf'                         *
 ******************************************************************************/
void err_fun(double *nom_x, double *delta_x, double *out_455516311871516666) {
   out_455516311871516666[0] = delta_x[0] + nom_x[0];
   out_455516311871516666[1] = delta_x[1] + nom_x[1];
   out_455516311871516666[2] = delta_x[2] + nom_x[2];
   out_455516311871516666[3] = delta_x[3] + nom_x[3];
   out_455516311871516666[4] = delta_x[4] + nom_x[4];
   out_455516311871516666[5] = delta_x[5] + nom_x[5];
   out_455516311871516666[6] = delta_x[6] + nom_x[6];
   out_455516311871516666[7] = delta_x[7] + nom_x[7];
   out_455516311871516666[8] = delta_x[8] + nom_x[8];
   out_455516311871516666[9] = delta_x[9] + nom_x[9];
   out_455516311871516666[10] = delta_x[10] + nom_x[10];
   out_455516311871516666[11] = delta_x[11] + nom_x[11];
   out_455516311871516666[12] = delta_x[12] + nom_x[12];
   out_455516311871516666[13] = delta_x[13] + nom_x[13];
   out_455516311871516666[14] = delta_x[14] + nom_x[14];
   out_455516311871516666[15] = delta_x[15] + nom_x[15];
   out_455516311871516666[16] = delta_x[16] + nom_x[16];
   out_455516311871516666[17] = delta_x[17] + nom_x[17];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_4129318549302704896) {
   out_4129318549302704896[0] = -nom_x[0] + true_x[0];
   out_4129318549302704896[1] = -nom_x[1] + true_x[1];
   out_4129318549302704896[2] = -nom_x[2] + true_x[2];
   out_4129318549302704896[3] = -nom_x[3] + true_x[3];
   out_4129318549302704896[4] = -nom_x[4] + true_x[4];
   out_4129318549302704896[5] = -nom_x[5] + true_x[5];
   out_4129318549302704896[6] = -nom_x[6] + true_x[6];
   out_4129318549302704896[7] = -nom_x[7] + true_x[7];
   out_4129318549302704896[8] = -nom_x[8] + true_x[8];
   out_4129318549302704896[9] = -nom_x[9] + true_x[9];
   out_4129318549302704896[10] = -nom_x[10] + true_x[10];
   out_4129318549302704896[11] = -nom_x[11] + true_x[11];
   out_4129318549302704896[12] = -nom_x[12] + true_x[12];
   out_4129318549302704896[13] = -nom_x[13] + true_x[13];
   out_4129318549302704896[14] = -nom_x[14] + true_x[14];
   out_4129318549302704896[15] = -nom_x[15] + true_x[15];
   out_4129318549302704896[16] = -nom_x[16] + true_x[16];
   out_4129318549302704896[17] = -nom_x[17] + true_x[17];
}
void H_mod_fun(double *state, double *out_291361178655748996) {
   out_291361178655748996[0] = 1.0;
   out_291361178655748996[1] = 0.0;
   out_291361178655748996[2] = 0.0;
   out_291361178655748996[3] = 0.0;
   out_291361178655748996[4] = 0.0;
   out_291361178655748996[5] = 0.0;
   out_291361178655748996[6] = 0.0;
   out_291361178655748996[7] = 0.0;
   out_291361178655748996[8] = 0.0;
   out_291361178655748996[9] = 0.0;
   out_291361178655748996[10] = 0.0;
   out_291361178655748996[11] = 0.0;
   out_291361178655748996[12] = 0.0;
   out_291361178655748996[13] = 0.0;
   out_291361178655748996[14] = 0.0;
   out_291361178655748996[15] = 0.0;
   out_291361178655748996[16] = 0.0;
   out_291361178655748996[17] = 0.0;
   out_291361178655748996[18] = 0.0;
   out_291361178655748996[19] = 1.0;
   out_291361178655748996[20] = 0.0;
   out_291361178655748996[21] = 0.0;
   out_291361178655748996[22] = 0.0;
   out_291361178655748996[23] = 0.0;
   out_291361178655748996[24] = 0.0;
   out_291361178655748996[25] = 0.0;
   out_291361178655748996[26] = 0.0;
   out_291361178655748996[27] = 0.0;
   out_291361178655748996[28] = 0.0;
   out_291361178655748996[29] = 0.0;
   out_291361178655748996[30] = 0.0;
   out_291361178655748996[31] = 0.0;
   out_291361178655748996[32] = 0.0;
   out_291361178655748996[33] = 0.0;
   out_291361178655748996[34] = 0.0;
   out_291361178655748996[35] = 0.0;
   out_291361178655748996[36] = 0.0;
   out_291361178655748996[37] = 0.0;
   out_291361178655748996[38] = 1.0;
   out_291361178655748996[39] = 0.0;
   out_291361178655748996[40] = 0.0;
   out_291361178655748996[41] = 0.0;
   out_291361178655748996[42] = 0.0;
   out_291361178655748996[43] = 0.0;
   out_291361178655748996[44] = 0.0;
   out_291361178655748996[45] = 0.0;
   out_291361178655748996[46] = 0.0;
   out_291361178655748996[47] = 0.0;
   out_291361178655748996[48] = 0.0;
   out_291361178655748996[49] = 0.0;
   out_291361178655748996[50] = 0.0;
   out_291361178655748996[51] = 0.0;
   out_291361178655748996[52] = 0.0;
   out_291361178655748996[53] = 0.0;
   out_291361178655748996[54] = 0.0;
   out_291361178655748996[55] = 0.0;
   out_291361178655748996[56] = 0.0;
   out_291361178655748996[57] = 1.0;
   out_291361178655748996[58] = 0.0;
   out_291361178655748996[59] = 0.0;
   out_291361178655748996[60] = 0.0;
   out_291361178655748996[61] = 0.0;
   out_291361178655748996[62] = 0.0;
   out_291361178655748996[63] = 0.0;
   out_291361178655748996[64] = 0.0;
   out_291361178655748996[65] = 0.0;
   out_291361178655748996[66] = 0.0;
   out_291361178655748996[67] = 0.0;
   out_291361178655748996[68] = 0.0;
   out_291361178655748996[69] = 0.0;
   out_291361178655748996[70] = 0.0;
   out_291361178655748996[71] = 0.0;
   out_291361178655748996[72] = 0.0;
   out_291361178655748996[73] = 0.0;
   out_291361178655748996[74] = 0.0;
   out_291361178655748996[75] = 0.0;
   out_291361178655748996[76] = 1.0;
   out_291361178655748996[77] = 0.0;
   out_291361178655748996[78] = 0.0;
   out_291361178655748996[79] = 0.0;
   out_291361178655748996[80] = 0.0;
   out_291361178655748996[81] = 0.0;
   out_291361178655748996[82] = 0.0;
   out_291361178655748996[83] = 0.0;
   out_291361178655748996[84] = 0.0;
   out_291361178655748996[85] = 0.0;
   out_291361178655748996[86] = 0.0;
   out_291361178655748996[87] = 0.0;
   out_291361178655748996[88] = 0.0;
   out_291361178655748996[89] = 0.0;
   out_291361178655748996[90] = 0.0;
   out_291361178655748996[91] = 0.0;
   out_291361178655748996[92] = 0.0;
   out_291361178655748996[93] = 0.0;
   out_291361178655748996[94] = 0.0;
   out_291361178655748996[95] = 1.0;
   out_291361178655748996[96] = 0.0;
   out_291361178655748996[97] = 0.0;
   out_291361178655748996[98] = 0.0;
   out_291361178655748996[99] = 0.0;
   out_291361178655748996[100] = 0.0;
   out_291361178655748996[101] = 0.0;
   out_291361178655748996[102] = 0.0;
   out_291361178655748996[103] = 0.0;
   out_291361178655748996[104] = 0.0;
   out_291361178655748996[105] = 0.0;
   out_291361178655748996[106] = 0.0;
   out_291361178655748996[107] = 0.0;
   out_291361178655748996[108] = 0.0;
   out_291361178655748996[109] = 0.0;
   out_291361178655748996[110] = 0.0;
   out_291361178655748996[111] = 0.0;
   out_291361178655748996[112] = 0.0;
   out_291361178655748996[113] = 0.0;
   out_291361178655748996[114] = 1.0;
   out_291361178655748996[115] = 0.0;
   out_291361178655748996[116] = 0.0;
   out_291361178655748996[117] = 0.0;
   out_291361178655748996[118] = 0.0;
   out_291361178655748996[119] = 0.0;
   out_291361178655748996[120] = 0.0;
   out_291361178655748996[121] = 0.0;
   out_291361178655748996[122] = 0.0;
   out_291361178655748996[123] = 0.0;
   out_291361178655748996[124] = 0.0;
   out_291361178655748996[125] = 0.0;
   out_291361178655748996[126] = 0.0;
   out_291361178655748996[127] = 0.0;
   out_291361178655748996[128] = 0.0;
   out_291361178655748996[129] = 0.0;
   out_291361178655748996[130] = 0.0;
   out_291361178655748996[131] = 0.0;
   out_291361178655748996[132] = 0.0;
   out_291361178655748996[133] = 1.0;
   out_291361178655748996[134] = 0.0;
   out_291361178655748996[135] = 0.0;
   out_291361178655748996[136] = 0.0;
   out_291361178655748996[137] = 0.0;
   out_291361178655748996[138] = 0.0;
   out_291361178655748996[139] = 0.0;
   out_291361178655748996[140] = 0.0;
   out_291361178655748996[141] = 0.0;
   out_291361178655748996[142] = 0.0;
   out_291361178655748996[143] = 0.0;
   out_291361178655748996[144] = 0.0;
   out_291361178655748996[145] = 0.0;
   out_291361178655748996[146] = 0.0;
   out_291361178655748996[147] = 0.0;
   out_291361178655748996[148] = 0.0;
   out_291361178655748996[149] = 0.0;
   out_291361178655748996[150] = 0.0;
   out_291361178655748996[151] = 0.0;
   out_291361178655748996[152] = 1.0;
   out_291361178655748996[153] = 0.0;
   out_291361178655748996[154] = 0.0;
   out_291361178655748996[155] = 0.0;
   out_291361178655748996[156] = 0.0;
   out_291361178655748996[157] = 0.0;
   out_291361178655748996[158] = 0.0;
   out_291361178655748996[159] = 0.0;
   out_291361178655748996[160] = 0.0;
   out_291361178655748996[161] = 0.0;
   out_291361178655748996[162] = 0.0;
   out_291361178655748996[163] = 0.0;
   out_291361178655748996[164] = 0.0;
   out_291361178655748996[165] = 0.0;
   out_291361178655748996[166] = 0.0;
   out_291361178655748996[167] = 0.0;
   out_291361178655748996[168] = 0.0;
   out_291361178655748996[169] = 0.0;
   out_291361178655748996[170] = 0.0;
   out_291361178655748996[171] = 1.0;
   out_291361178655748996[172] = 0.0;
   out_291361178655748996[173] = 0.0;
   out_291361178655748996[174] = 0.0;
   out_291361178655748996[175] = 0.0;
   out_291361178655748996[176] = 0.0;
   out_291361178655748996[177] = 0.0;
   out_291361178655748996[178] = 0.0;
   out_291361178655748996[179] = 0.0;
   out_291361178655748996[180] = 0.0;
   out_291361178655748996[181] = 0.0;
   out_291361178655748996[182] = 0.0;
   out_291361178655748996[183] = 0.0;
   out_291361178655748996[184] = 0.0;
   out_291361178655748996[185] = 0.0;
   out_291361178655748996[186] = 0.0;
   out_291361178655748996[187] = 0.0;
   out_291361178655748996[188] = 0.0;
   out_291361178655748996[189] = 0.0;
   out_291361178655748996[190] = 1.0;
   out_291361178655748996[191] = 0.0;
   out_291361178655748996[192] = 0.0;
   out_291361178655748996[193] = 0.0;
   out_291361178655748996[194] = 0.0;
   out_291361178655748996[195] = 0.0;
   out_291361178655748996[196] = 0.0;
   out_291361178655748996[197] = 0.0;
   out_291361178655748996[198] = 0.0;
   out_291361178655748996[199] = 0.0;
   out_291361178655748996[200] = 0.0;
   out_291361178655748996[201] = 0.0;
   out_291361178655748996[202] = 0.0;
   out_291361178655748996[203] = 0.0;
   out_291361178655748996[204] = 0.0;
   out_291361178655748996[205] = 0.0;
   out_291361178655748996[206] = 0.0;
   out_291361178655748996[207] = 0.0;
   out_291361178655748996[208] = 0.0;
   out_291361178655748996[209] = 1.0;
   out_291361178655748996[210] = 0.0;
   out_291361178655748996[211] = 0.0;
   out_291361178655748996[212] = 0.0;
   out_291361178655748996[213] = 0.0;
   out_291361178655748996[214] = 0.0;
   out_291361178655748996[215] = 0.0;
   out_291361178655748996[216] = 0.0;
   out_291361178655748996[217] = 0.0;
   out_291361178655748996[218] = 0.0;
   out_291361178655748996[219] = 0.0;
   out_291361178655748996[220] = 0.0;
   out_291361178655748996[221] = 0.0;
   out_291361178655748996[222] = 0.0;
   out_291361178655748996[223] = 0.0;
   out_291361178655748996[224] = 0.0;
   out_291361178655748996[225] = 0.0;
   out_291361178655748996[226] = 0.0;
   out_291361178655748996[227] = 0.0;
   out_291361178655748996[228] = 1.0;
   out_291361178655748996[229] = 0.0;
   out_291361178655748996[230] = 0.0;
   out_291361178655748996[231] = 0.0;
   out_291361178655748996[232] = 0.0;
   out_291361178655748996[233] = 0.0;
   out_291361178655748996[234] = 0.0;
   out_291361178655748996[235] = 0.0;
   out_291361178655748996[236] = 0.0;
   out_291361178655748996[237] = 0.0;
   out_291361178655748996[238] = 0.0;
   out_291361178655748996[239] = 0.0;
   out_291361178655748996[240] = 0.0;
   out_291361178655748996[241] = 0.0;
   out_291361178655748996[242] = 0.0;
   out_291361178655748996[243] = 0.0;
   out_291361178655748996[244] = 0.0;
   out_291361178655748996[245] = 0.0;
   out_291361178655748996[246] = 0.0;
   out_291361178655748996[247] = 1.0;
   out_291361178655748996[248] = 0.0;
   out_291361178655748996[249] = 0.0;
   out_291361178655748996[250] = 0.0;
   out_291361178655748996[251] = 0.0;
   out_291361178655748996[252] = 0.0;
   out_291361178655748996[253] = 0.0;
   out_291361178655748996[254] = 0.0;
   out_291361178655748996[255] = 0.0;
   out_291361178655748996[256] = 0.0;
   out_291361178655748996[257] = 0.0;
   out_291361178655748996[258] = 0.0;
   out_291361178655748996[259] = 0.0;
   out_291361178655748996[260] = 0.0;
   out_291361178655748996[261] = 0.0;
   out_291361178655748996[262] = 0.0;
   out_291361178655748996[263] = 0.0;
   out_291361178655748996[264] = 0.0;
   out_291361178655748996[265] = 0.0;
   out_291361178655748996[266] = 1.0;
   out_291361178655748996[267] = 0.0;
   out_291361178655748996[268] = 0.0;
   out_291361178655748996[269] = 0.0;
   out_291361178655748996[270] = 0.0;
   out_291361178655748996[271] = 0.0;
   out_291361178655748996[272] = 0.0;
   out_291361178655748996[273] = 0.0;
   out_291361178655748996[274] = 0.0;
   out_291361178655748996[275] = 0.0;
   out_291361178655748996[276] = 0.0;
   out_291361178655748996[277] = 0.0;
   out_291361178655748996[278] = 0.0;
   out_291361178655748996[279] = 0.0;
   out_291361178655748996[280] = 0.0;
   out_291361178655748996[281] = 0.0;
   out_291361178655748996[282] = 0.0;
   out_291361178655748996[283] = 0.0;
   out_291361178655748996[284] = 0.0;
   out_291361178655748996[285] = 1.0;
   out_291361178655748996[286] = 0.0;
   out_291361178655748996[287] = 0.0;
   out_291361178655748996[288] = 0.0;
   out_291361178655748996[289] = 0.0;
   out_291361178655748996[290] = 0.0;
   out_291361178655748996[291] = 0.0;
   out_291361178655748996[292] = 0.0;
   out_291361178655748996[293] = 0.0;
   out_291361178655748996[294] = 0.0;
   out_291361178655748996[295] = 0.0;
   out_291361178655748996[296] = 0.0;
   out_291361178655748996[297] = 0.0;
   out_291361178655748996[298] = 0.0;
   out_291361178655748996[299] = 0.0;
   out_291361178655748996[300] = 0.0;
   out_291361178655748996[301] = 0.0;
   out_291361178655748996[302] = 0.0;
   out_291361178655748996[303] = 0.0;
   out_291361178655748996[304] = 1.0;
   out_291361178655748996[305] = 0.0;
   out_291361178655748996[306] = 0.0;
   out_291361178655748996[307] = 0.0;
   out_291361178655748996[308] = 0.0;
   out_291361178655748996[309] = 0.0;
   out_291361178655748996[310] = 0.0;
   out_291361178655748996[311] = 0.0;
   out_291361178655748996[312] = 0.0;
   out_291361178655748996[313] = 0.0;
   out_291361178655748996[314] = 0.0;
   out_291361178655748996[315] = 0.0;
   out_291361178655748996[316] = 0.0;
   out_291361178655748996[317] = 0.0;
   out_291361178655748996[318] = 0.0;
   out_291361178655748996[319] = 0.0;
   out_291361178655748996[320] = 0.0;
   out_291361178655748996[321] = 0.0;
   out_291361178655748996[322] = 0.0;
   out_291361178655748996[323] = 1.0;
}
void f_fun(double *state, double dt, double *out_6277713955818918611) {
   out_6277713955818918611[0] = atan2((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), -(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]));
   out_6277713955818918611[1] = asin(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]));
   out_6277713955818918611[2] = atan2(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), -(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]));
   out_6277713955818918611[3] = dt*state[12] + state[3];
   out_6277713955818918611[4] = dt*state[13] + state[4];
   out_6277713955818918611[5] = dt*state[14] + state[5];
   out_6277713955818918611[6] = state[6];
   out_6277713955818918611[7] = state[7];
   out_6277713955818918611[8] = state[8];
   out_6277713955818918611[9] = state[9];
   out_6277713955818918611[10] = state[10];
   out_6277713955818918611[11] = state[11];
   out_6277713955818918611[12] = state[12];
   out_6277713955818918611[13] = state[13];
   out_6277713955818918611[14] = state[14];
   out_6277713955818918611[15] = state[15];
   out_6277713955818918611[16] = state[16];
   out_6277713955818918611[17] = state[17];
}
void F_fun(double *state, double dt, double *out_3051886930390844105) {
   out_3051886930390844105[0] = ((-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*cos(state[0])*cos(state[1]) - sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*cos(state[0])*cos(state[1]) - sin(dt*state[6])*sin(state[0])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_3051886930390844105[1] = ((-sin(dt*state[6])*sin(dt*state[8]) - sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*cos(state[1]) - (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*sin(state[1]) - sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(state[0]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*sin(state[1]) + (-sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) + sin(dt*state[8])*cos(dt*state[6]))*cos(state[1]) - sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(state[0]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_3051886930390844105[2] = 0;
   out_3051886930390844105[3] = 0;
   out_3051886930390844105[4] = 0;
   out_3051886930390844105[5] = 0;
   out_3051886930390844105[6] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(dt*cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) - dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_3051886930390844105[7] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*sin(dt*state[7])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[6])*sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) - dt*sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[7])*cos(dt*state[6])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[8])*sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]) - dt*sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_3051886930390844105[8] = ((dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((dt*sin(dt*state[6])*sin(dt*state[8]) + dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_3051886930390844105[9] = 0;
   out_3051886930390844105[10] = 0;
   out_3051886930390844105[11] = 0;
   out_3051886930390844105[12] = 0;
   out_3051886930390844105[13] = 0;
   out_3051886930390844105[14] = 0;
   out_3051886930390844105[15] = 0;
   out_3051886930390844105[16] = 0;
   out_3051886930390844105[17] = 0;
   out_3051886930390844105[18] = (-sin(dt*state[7])*sin(state[0])*cos(state[1]) - sin(dt*state[8])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_3051886930390844105[19] = (-sin(dt*state[7])*sin(state[1])*cos(state[0]) + sin(dt*state[8])*sin(state[0])*sin(state[1])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_3051886930390844105[20] = 0;
   out_3051886930390844105[21] = 0;
   out_3051886930390844105[22] = 0;
   out_3051886930390844105[23] = 0;
   out_3051886930390844105[24] = 0;
   out_3051886930390844105[25] = (dt*sin(dt*state[7])*sin(dt*state[8])*sin(state[0])*cos(state[1]) - dt*sin(dt*state[7])*sin(state[1])*cos(dt*state[8]) + dt*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_3051886930390844105[26] = (-dt*sin(dt*state[8])*sin(state[1])*cos(dt*state[7]) - dt*sin(state[0])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_3051886930390844105[27] = 0;
   out_3051886930390844105[28] = 0;
   out_3051886930390844105[29] = 0;
   out_3051886930390844105[30] = 0;
   out_3051886930390844105[31] = 0;
   out_3051886930390844105[32] = 0;
   out_3051886930390844105[33] = 0;
   out_3051886930390844105[34] = 0;
   out_3051886930390844105[35] = 0;
   out_3051886930390844105[36] = ((sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_3051886930390844105[37] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-sin(dt*state[7])*sin(state[2])*cos(state[0])*cos(state[1]) + sin(dt*state[8])*sin(state[0])*sin(state[2])*cos(dt*state[7])*cos(state[1]) - sin(state[1])*sin(state[2])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(-sin(dt*state[7])*cos(state[0])*cos(state[1])*cos(state[2]) + sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1])*cos(state[2]) - sin(state[1])*cos(dt*state[7])*cos(dt*state[8])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_3051886930390844105[38] = ((-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (-sin(state[0])*sin(state[1])*sin(state[2]) - cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_3051886930390844105[39] = 0;
   out_3051886930390844105[40] = 0;
   out_3051886930390844105[41] = 0;
   out_3051886930390844105[42] = 0;
   out_3051886930390844105[43] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(dt*(sin(state[0])*cos(state[2]) - sin(state[1])*sin(state[2])*cos(state[0]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*sin(state[2])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(dt*(-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_3051886930390844105[44] = (dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*sin(state[2])*cos(dt*state[7])*cos(state[1]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + (dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[7])*cos(state[1])*cos(state[2]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_3051886930390844105[45] = 0;
   out_3051886930390844105[46] = 0;
   out_3051886930390844105[47] = 0;
   out_3051886930390844105[48] = 0;
   out_3051886930390844105[49] = 0;
   out_3051886930390844105[50] = 0;
   out_3051886930390844105[51] = 0;
   out_3051886930390844105[52] = 0;
   out_3051886930390844105[53] = 0;
   out_3051886930390844105[54] = 0;
   out_3051886930390844105[55] = 0;
   out_3051886930390844105[56] = 0;
   out_3051886930390844105[57] = 1;
   out_3051886930390844105[58] = 0;
   out_3051886930390844105[59] = 0;
   out_3051886930390844105[60] = 0;
   out_3051886930390844105[61] = 0;
   out_3051886930390844105[62] = 0;
   out_3051886930390844105[63] = 0;
   out_3051886930390844105[64] = 0;
   out_3051886930390844105[65] = 0;
   out_3051886930390844105[66] = dt;
   out_3051886930390844105[67] = 0;
   out_3051886930390844105[68] = 0;
   out_3051886930390844105[69] = 0;
   out_3051886930390844105[70] = 0;
   out_3051886930390844105[71] = 0;
   out_3051886930390844105[72] = 0;
   out_3051886930390844105[73] = 0;
   out_3051886930390844105[74] = 0;
   out_3051886930390844105[75] = 0;
   out_3051886930390844105[76] = 1;
   out_3051886930390844105[77] = 0;
   out_3051886930390844105[78] = 0;
   out_3051886930390844105[79] = 0;
   out_3051886930390844105[80] = 0;
   out_3051886930390844105[81] = 0;
   out_3051886930390844105[82] = 0;
   out_3051886930390844105[83] = 0;
   out_3051886930390844105[84] = 0;
   out_3051886930390844105[85] = dt;
   out_3051886930390844105[86] = 0;
   out_3051886930390844105[87] = 0;
   out_3051886930390844105[88] = 0;
   out_3051886930390844105[89] = 0;
   out_3051886930390844105[90] = 0;
   out_3051886930390844105[91] = 0;
   out_3051886930390844105[92] = 0;
   out_3051886930390844105[93] = 0;
   out_3051886930390844105[94] = 0;
   out_3051886930390844105[95] = 1;
   out_3051886930390844105[96] = 0;
   out_3051886930390844105[97] = 0;
   out_3051886930390844105[98] = 0;
   out_3051886930390844105[99] = 0;
   out_3051886930390844105[100] = 0;
   out_3051886930390844105[101] = 0;
   out_3051886930390844105[102] = 0;
   out_3051886930390844105[103] = 0;
   out_3051886930390844105[104] = dt;
   out_3051886930390844105[105] = 0;
   out_3051886930390844105[106] = 0;
   out_3051886930390844105[107] = 0;
   out_3051886930390844105[108] = 0;
   out_3051886930390844105[109] = 0;
   out_3051886930390844105[110] = 0;
   out_3051886930390844105[111] = 0;
   out_3051886930390844105[112] = 0;
   out_3051886930390844105[113] = 0;
   out_3051886930390844105[114] = 1;
   out_3051886930390844105[115] = 0;
   out_3051886930390844105[116] = 0;
   out_3051886930390844105[117] = 0;
   out_3051886930390844105[118] = 0;
   out_3051886930390844105[119] = 0;
   out_3051886930390844105[120] = 0;
   out_3051886930390844105[121] = 0;
   out_3051886930390844105[122] = 0;
   out_3051886930390844105[123] = 0;
   out_3051886930390844105[124] = 0;
   out_3051886930390844105[125] = 0;
   out_3051886930390844105[126] = 0;
   out_3051886930390844105[127] = 0;
   out_3051886930390844105[128] = 0;
   out_3051886930390844105[129] = 0;
   out_3051886930390844105[130] = 0;
   out_3051886930390844105[131] = 0;
   out_3051886930390844105[132] = 0;
   out_3051886930390844105[133] = 1;
   out_3051886930390844105[134] = 0;
   out_3051886930390844105[135] = 0;
   out_3051886930390844105[136] = 0;
   out_3051886930390844105[137] = 0;
   out_3051886930390844105[138] = 0;
   out_3051886930390844105[139] = 0;
   out_3051886930390844105[140] = 0;
   out_3051886930390844105[141] = 0;
   out_3051886930390844105[142] = 0;
   out_3051886930390844105[143] = 0;
   out_3051886930390844105[144] = 0;
   out_3051886930390844105[145] = 0;
   out_3051886930390844105[146] = 0;
   out_3051886930390844105[147] = 0;
   out_3051886930390844105[148] = 0;
   out_3051886930390844105[149] = 0;
   out_3051886930390844105[150] = 0;
   out_3051886930390844105[151] = 0;
   out_3051886930390844105[152] = 1;
   out_3051886930390844105[153] = 0;
   out_3051886930390844105[154] = 0;
   out_3051886930390844105[155] = 0;
   out_3051886930390844105[156] = 0;
   out_3051886930390844105[157] = 0;
   out_3051886930390844105[158] = 0;
   out_3051886930390844105[159] = 0;
   out_3051886930390844105[160] = 0;
   out_3051886930390844105[161] = 0;
   out_3051886930390844105[162] = 0;
   out_3051886930390844105[163] = 0;
   out_3051886930390844105[164] = 0;
   out_3051886930390844105[165] = 0;
   out_3051886930390844105[166] = 0;
   out_3051886930390844105[167] = 0;
   out_3051886930390844105[168] = 0;
   out_3051886930390844105[169] = 0;
   out_3051886930390844105[170] = 0;
   out_3051886930390844105[171] = 1;
   out_3051886930390844105[172] = 0;
   out_3051886930390844105[173] = 0;
   out_3051886930390844105[174] = 0;
   out_3051886930390844105[175] = 0;
   out_3051886930390844105[176] = 0;
   out_3051886930390844105[177] = 0;
   out_3051886930390844105[178] = 0;
   out_3051886930390844105[179] = 0;
   out_3051886930390844105[180] = 0;
   out_3051886930390844105[181] = 0;
   out_3051886930390844105[182] = 0;
   out_3051886930390844105[183] = 0;
   out_3051886930390844105[184] = 0;
   out_3051886930390844105[185] = 0;
   out_3051886930390844105[186] = 0;
   out_3051886930390844105[187] = 0;
   out_3051886930390844105[188] = 0;
   out_3051886930390844105[189] = 0;
   out_3051886930390844105[190] = 1;
   out_3051886930390844105[191] = 0;
   out_3051886930390844105[192] = 0;
   out_3051886930390844105[193] = 0;
   out_3051886930390844105[194] = 0;
   out_3051886930390844105[195] = 0;
   out_3051886930390844105[196] = 0;
   out_3051886930390844105[197] = 0;
   out_3051886930390844105[198] = 0;
   out_3051886930390844105[199] = 0;
   out_3051886930390844105[200] = 0;
   out_3051886930390844105[201] = 0;
   out_3051886930390844105[202] = 0;
   out_3051886930390844105[203] = 0;
   out_3051886930390844105[204] = 0;
   out_3051886930390844105[205] = 0;
   out_3051886930390844105[206] = 0;
   out_3051886930390844105[207] = 0;
   out_3051886930390844105[208] = 0;
   out_3051886930390844105[209] = 1;
   out_3051886930390844105[210] = 0;
   out_3051886930390844105[211] = 0;
   out_3051886930390844105[212] = 0;
   out_3051886930390844105[213] = 0;
   out_3051886930390844105[214] = 0;
   out_3051886930390844105[215] = 0;
   out_3051886930390844105[216] = 0;
   out_3051886930390844105[217] = 0;
   out_3051886930390844105[218] = 0;
   out_3051886930390844105[219] = 0;
   out_3051886930390844105[220] = 0;
   out_3051886930390844105[221] = 0;
   out_3051886930390844105[222] = 0;
   out_3051886930390844105[223] = 0;
   out_3051886930390844105[224] = 0;
   out_3051886930390844105[225] = 0;
   out_3051886930390844105[226] = 0;
   out_3051886930390844105[227] = 0;
   out_3051886930390844105[228] = 1;
   out_3051886930390844105[229] = 0;
   out_3051886930390844105[230] = 0;
   out_3051886930390844105[231] = 0;
   out_3051886930390844105[232] = 0;
   out_3051886930390844105[233] = 0;
   out_3051886930390844105[234] = 0;
   out_3051886930390844105[235] = 0;
   out_3051886930390844105[236] = 0;
   out_3051886930390844105[237] = 0;
   out_3051886930390844105[238] = 0;
   out_3051886930390844105[239] = 0;
   out_3051886930390844105[240] = 0;
   out_3051886930390844105[241] = 0;
   out_3051886930390844105[242] = 0;
   out_3051886930390844105[243] = 0;
   out_3051886930390844105[244] = 0;
   out_3051886930390844105[245] = 0;
   out_3051886930390844105[246] = 0;
   out_3051886930390844105[247] = 1;
   out_3051886930390844105[248] = 0;
   out_3051886930390844105[249] = 0;
   out_3051886930390844105[250] = 0;
   out_3051886930390844105[251] = 0;
   out_3051886930390844105[252] = 0;
   out_3051886930390844105[253] = 0;
   out_3051886930390844105[254] = 0;
   out_3051886930390844105[255] = 0;
   out_3051886930390844105[256] = 0;
   out_3051886930390844105[257] = 0;
   out_3051886930390844105[258] = 0;
   out_3051886930390844105[259] = 0;
   out_3051886930390844105[260] = 0;
   out_3051886930390844105[261] = 0;
   out_3051886930390844105[262] = 0;
   out_3051886930390844105[263] = 0;
   out_3051886930390844105[264] = 0;
   out_3051886930390844105[265] = 0;
   out_3051886930390844105[266] = 1;
   out_3051886930390844105[267] = 0;
   out_3051886930390844105[268] = 0;
   out_3051886930390844105[269] = 0;
   out_3051886930390844105[270] = 0;
   out_3051886930390844105[271] = 0;
   out_3051886930390844105[272] = 0;
   out_3051886930390844105[273] = 0;
   out_3051886930390844105[274] = 0;
   out_3051886930390844105[275] = 0;
   out_3051886930390844105[276] = 0;
   out_3051886930390844105[277] = 0;
   out_3051886930390844105[278] = 0;
   out_3051886930390844105[279] = 0;
   out_3051886930390844105[280] = 0;
   out_3051886930390844105[281] = 0;
   out_3051886930390844105[282] = 0;
   out_3051886930390844105[283] = 0;
   out_3051886930390844105[284] = 0;
   out_3051886930390844105[285] = 1;
   out_3051886930390844105[286] = 0;
   out_3051886930390844105[287] = 0;
   out_3051886930390844105[288] = 0;
   out_3051886930390844105[289] = 0;
   out_3051886930390844105[290] = 0;
   out_3051886930390844105[291] = 0;
   out_3051886930390844105[292] = 0;
   out_3051886930390844105[293] = 0;
   out_3051886930390844105[294] = 0;
   out_3051886930390844105[295] = 0;
   out_3051886930390844105[296] = 0;
   out_3051886930390844105[297] = 0;
   out_3051886930390844105[298] = 0;
   out_3051886930390844105[299] = 0;
   out_3051886930390844105[300] = 0;
   out_3051886930390844105[301] = 0;
   out_3051886930390844105[302] = 0;
   out_3051886930390844105[303] = 0;
   out_3051886930390844105[304] = 1;
   out_3051886930390844105[305] = 0;
   out_3051886930390844105[306] = 0;
   out_3051886930390844105[307] = 0;
   out_3051886930390844105[308] = 0;
   out_3051886930390844105[309] = 0;
   out_3051886930390844105[310] = 0;
   out_3051886930390844105[311] = 0;
   out_3051886930390844105[312] = 0;
   out_3051886930390844105[313] = 0;
   out_3051886930390844105[314] = 0;
   out_3051886930390844105[315] = 0;
   out_3051886930390844105[316] = 0;
   out_3051886930390844105[317] = 0;
   out_3051886930390844105[318] = 0;
   out_3051886930390844105[319] = 0;
   out_3051886930390844105[320] = 0;
   out_3051886930390844105[321] = 0;
   out_3051886930390844105[322] = 0;
   out_3051886930390844105[323] = 1;
}
void h_4(double *state, double *unused, double *out_1179958653059836279) {
   out_1179958653059836279[0] = state[6] + state[9];
   out_1179958653059836279[1] = state[7] + state[10];
   out_1179958653059836279[2] = state[8] + state[11];
}
void H_4(double *state, double *unused, double *out_3634206011302561399) {
   out_3634206011302561399[0] = 0;
   out_3634206011302561399[1] = 0;
   out_3634206011302561399[2] = 0;
   out_3634206011302561399[3] = 0;
   out_3634206011302561399[4] = 0;
   out_3634206011302561399[5] = 0;
   out_3634206011302561399[6] = 1;
   out_3634206011302561399[7] = 0;
   out_3634206011302561399[8] = 0;
   out_3634206011302561399[9] = 1;
   out_3634206011302561399[10] = 0;
   out_3634206011302561399[11] = 0;
   out_3634206011302561399[12] = 0;
   out_3634206011302561399[13] = 0;
   out_3634206011302561399[14] = 0;
   out_3634206011302561399[15] = 0;
   out_3634206011302561399[16] = 0;
   out_3634206011302561399[17] = 0;
   out_3634206011302561399[18] = 0;
   out_3634206011302561399[19] = 0;
   out_3634206011302561399[20] = 0;
   out_3634206011302561399[21] = 0;
   out_3634206011302561399[22] = 0;
   out_3634206011302561399[23] = 0;
   out_3634206011302561399[24] = 0;
   out_3634206011302561399[25] = 1;
   out_3634206011302561399[26] = 0;
   out_3634206011302561399[27] = 0;
   out_3634206011302561399[28] = 1;
   out_3634206011302561399[29] = 0;
   out_3634206011302561399[30] = 0;
   out_3634206011302561399[31] = 0;
   out_3634206011302561399[32] = 0;
   out_3634206011302561399[33] = 0;
   out_3634206011302561399[34] = 0;
   out_3634206011302561399[35] = 0;
   out_3634206011302561399[36] = 0;
   out_3634206011302561399[37] = 0;
   out_3634206011302561399[38] = 0;
   out_3634206011302561399[39] = 0;
   out_3634206011302561399[40] = 0;
   out_3634206011302561399[41] = 0;
   out_3634206011302561399[42] = 0;
   out_3634206011302561399[43] = 0;
   out_3634206011302561399[44] = 1;
   out_3634206011302561399[45] = 0;
   out_3634206011302561399[46] = 0;
   out_3634206011302561399[47] = 1;
   out_3634206011302561399[48] = 0;
   out_3634206011302561399[49] = 0;
   out_3634206011302561399[50] = 0;
   out_3634206011302561399[51] = 0;
   out_3634206011302561399[52] = 0;
   out_3634206011302561399[53] = 0;
}
void h_10(double *state, double *unused, double *out_7917951398739470562) {
   out_7917951398739470562[0] = 9.8100000000000005*sin(state[1]) - state[4]*state[8] + state[5]*state[7] + state[12] + state[15];
   out_7917951398739470562[1] = -9.8100000000000005*sin(state[0])*cos(state[1]) + state[3]*state[8] - state[5]*state[6] + state[13] + state[16];
   out_7917951398739470562[2] = -9.8100000000000005*cos(state[0])*cos(state[1]) - state[3]*state[7] + state[4]*state[6] + state[14] + state[17];
}
void H_10(double *state, double *unused, double *out_5574544512634486876) {
   out_5574544512634486876[0] = 0;
   out_5574544512634486876[1] = 9.8100000000000005*cos(state[1]);
   out_5574544512634486876[2] = 0;
   out_5574544512634486876[3] = 0;
   out_5574544512634486876[4] = -state[8];
   out_5574544512634486876[5] = state[7];
   out_5574544512634486876[6] = 0;
   out_5574544512634486876[7] = state[5];
   out_5574544512634486876[8] = -state[4];
   out_5574544512634486876[9] = 0;
   out_5574544512634486876[10] = 0;
   out_5574544512634486876[11] = 0;
   out_5574544512634486876[12] = 1;
   out_5574544512634486876[13] = 0;
   out_5574544512634486876[14] = 0;
   out_5574544512634486876[15] = 1;
   out_5574544512634486876[16] = 0;
   out_5574544512634486876[17] = 0;
   out_5574544512634486876[18] = -9.8100000000000005*cos(state[0])*cos(state[1]);
   out_5574544512634486876[19] = 9.8100000000000005*sin(state[0])*sin(state[1]);
   out_5574544512634486876[20] = 0;
   out_5574544512634486876[21] = state[8];
   out_5574544512634486876[22] = 0;
   out_5574544512634486876[23] = -state[6];
   out_5574544512634486876[24] = -state[5];
   out_5574544512634486876[25] = 0;
   out_5574544512634486876[26] = state[3];
   out_5574544512634486876[27] = 0;
   out_5574544512634486876[28] = 0;
   out_5574544512634486876[29] = 0;
   out_5574544512634486876[30] = 0;
   out_5574544512634486876[31] = 1;
   out_5574544512634486876[32] = 0;
   out_5574544512634486876[33] = 0;
   out_5574544512634486876[34] = 1;
   out_5574544512634486876[35] = 0;
   out_5574544512634486876[36] = 9.8100000000000005*sin(state[0])*cos(state[1]);
   out_5574544512634486876[37] = 9.8100000000000005*sin(state[1])*cos(state[0]);
   out_5574544512634486876[38] = 0;
   out_5574544512634486876[39] = -state[7];
   out_5574544512634486876[40] = state[6];
   out_5574544512634486876[41] = 0;
   out_5574544512634486876[42] = state[4];
   out_5574544512634486876[43] = -state[3];
   out_5574544512634486876[44] = 0;
   out_5574544512634486876[45] = 0;
   out_5574544512634486876[46] = 0;
   out_5574544512634486876[47] = 0;
   out_5574544512634486876[48] = 0;
   out_5574544512634486876[49] = 0;
   out_5574544512634486876[50] = 1;
   out_5574544512634486876[51] = 0;
   out_5574544512634486876[52] = 0;
   out_5574544512634486876[53] = 1;
}
void h_13(double *state, double *unused, double *out_7282516462007542478) {
   out_7282516462007542478[0] = state[3];
   out_7282516462007542478[1] = state[4];
   out_7282516462007542478[2] = state[5];
}
void H_13(double *state, double *unused, double *out_6846479836634894200) {
   out_6846479836634894200[0] = 0;
   out_6846479836634894200[1] = 0;
   out_6846479836634894200[2] = 0;
   out_6846479836634894200[3] = 1;
   out_6846479836634894200[4] = 0;
   out_6846479836634894200[5] = 0;
   out_6846479836634894200[6] = 0;
   out_6846479836634894200[7] = 0;
   out_6846479836634894200[8] = 0;
   out_6846479836634894200[9] = 0;
   out_6846479836634894200[10] = 0;
   out_6846479836634894200[11] = 0;
   out_6846479836634894200[12] = 0;
   out_6846479836634894200[13] = 0;
   out_6846479836634894200[14] = 0;
   out_6846479836634894200[15] = 0;
   out_6846479836634894200[16] = 0;
   out_6846479836634894200[17] = 0;
   out_6846479836634894200[18] = 0;
   out_6846479836634894200[19] = 0;
   out_6846479836634894200[20] = 0;
   out_6846479836634894200[21] = 0;
   out_6846479836634894200[22] = 1;
   out_6846479836634894200[23] = 0;
   out_6846479836634894200[24] = 0;
   out_6846479836634894200[25] = 0;
   out_6846479836634894200[26] = 0;
   out_6846479836634894200[27] = 0;
   out_6846479836634894200[28] = 0;
   out_6846479836634894200[29] = 0;
   out_6846479836634894200[30] = 0;
   out_6846479836634894200[31] = 0;
   out_6846479836634894200[32] = 0;
   out_6846479836634894200[33] = 0;
   out_6846479836634894200[34] = 0;
   out_6846479836634894200[35] = 0;
   out_6846479836634894200[36] = 0;
   out_6846479836634894200[37] = 0;
   out_6846479836634894200[38] = 0;
   out_6846479836634894200[39] = 0;
   out_6846479836634894200[40] = 0;
   out_6846479836634894200[41] = 1;
   out_6846479836634894200[42] = 0;
   out_6846479836634894200[43] = 0;
   out_6846479836634894200[44] = 0;
   out_6846479836634894200[45] = 0;
   out_6846479836634894200[46] = 0;
   out_6846479836634894200[47] = 0;
   out_6846479836634894200[48] = 0;
   out_6846479836634894200[49] = 0;
   out_6846479836634894200[50] = 0;
   out_6846479836634894200[51] = 0;
   out_6846479836634894200[52] = 0;
   out_6846479836634894200[53] = 0;
}
void h_14(double *state, double *unused, double *out_7084974374367104635) {
   out_7084974374367104635[0] = state[6];
   out_7084974374367104635[1] = state[7];
   out_7084974374367104635[2] = state[8];
}
void H_14(double *state, double *unused, double *out_551417579007189103) {
   out_551417579007189103[0] = 0;
   out_551417579007189103[1] = 0;
   out_551417579007189103[2] = 0;
   out_551417579007189103[3] = 0;
   out_551417579007189103[4] = 0;
   out_551417579007189103[5] = 0;
   out_551417579007189103[6] = 1;
   out_551417579007189103[7] = 0;
   out_551417579007189103[8] = 0;
   out_551417579007189103[9] = 0;
   out_551417579007189103[10] = 0;
   out_551417579007189103[11] = 0;
   out_551417579007189103[12] = 0;
   out_551417579007189103[13] = 0;
   out_551417579007189103[14] = 0;
   out_551417579007189103[15] = 0;
   out_551417579007189103[16] = 0;
   out_551417579007189103[17] = 0;
   out_551417579007189103[18] = 0;
   out_551417579007189103[19] = 0;
   out_551417579007189103[20] = 0;
   out_551417579007189103[21] = 0;
   out_551417579007189103[22] = 0;
   out_551417579007189103[23] = 0;
   out_551417579007189103[24] = 0;
   out_551417579007189103[25] = 1;
   out_551417579007189103[26] = 0;
   out_551417579007189103[27] = 0;
   out_551417579007189103[28] = 0;
   out_551417579007189103[29] = 0;
   out_551417579007189103[30] = 0;
   out_551417579007189103[31] = 0;
   out_551417579007189103[32] = 0;
   out_551417579007189103[33] = 0;
   out_551417579007189103[34] = 0;
   out_551417579007189103[35] = 0;
   out_551417579007189103[36] = 0;
   out_551417579007189103[37] = 0;
   out_551417579007189103[38] = 0;
   out_551417579007189103[39] = 0;
   out_551417579007189103[40] = 0;
   out_551417579007189103[41] = 0;
   out_551417579007189103[42] = 0;
   out_551417579007189103[43] = 0;
   out_551417579007189103[44] = 1;
   out_551417579007189103[45] = 0;
   out_551417579007189103[46] = 0;
   out_551417579007189103[47] = 0;
   out_551417579007189103[48] = 0;
   out_551417579007189103[49] = 0;
   out_551417579007189103[50] = 0;
   out_551417579007189103[51] = 0;
   out_551417579007189103[52] = 0;
   out_551417579007189103[53] = 0;
}
#include <eigen3/Eigen/Dense>
#include <iostream>

typedef Eigen::Matrix<double, DIM, DIM, Eigen::RowMajor> DDM;
typedef Eigen::Matrix<double, EDIM, EDIM, Eigen::RowMajor> EEM;
typedef Eigen::Matrix<double, DIM, EDIM, Eigen::RowMajor> DEM;

void predict(double *in_x, double *in_P, double *in_Q, double dt) {
  typedef Eigen::Matrix<double, MEDIM, MEDIM, Eigen::RowMajor> RRM;

  double nx[DIM] = {0};
  double in_F[EDIM*EDIM] = {0};

  // functions from sympy
  f_fun(in_x, dt, nx);
  F_fun(in_x, dt, in_F);


  EEM F(in_F);
  EEM P(in_P);
  EEM Q(in_Q);

  RRM F_main = F.topLeftCorner(MEDIM, MEDIM);
  P.topLeftCorner(MEDIM, MEDIM) = (F_main * P.topLeftCorner(MEDIM, MEDIM)) * F_main.transpose();
  P.topRightCorner(MEDIM, EDIM - MEDIM) = F_main * P.topRightCorner(MEDIM, EDIM - MEDIM);
  P.bottomLeftCorner(EDIM - MEDIM, MEDIM) = P.bottomLeftCorner(EDIM - MEDIM, MEDIM) * F_main.transpose();

  P = P + dt*Q;

  // copy out state
  memcpy(in_x, nx, DIM * sizeof(double));
  memcpy(in_P, P.data(), EDIM * EDIM * sizeof(double));
}

// note: extra_args dim only correct when null space projecting
// otherwise 1
template <int ZDIM, int EADIM, bool MAHA_TEST>
void update(double *in_x, double *in_P, Hfun h_fun, Hfun H_fun, Hfun Hea_fun, double *in_z, double *in_R, double *in_ea, double MAHA_THRESHOLD) {
  typedef Eigen::Matrix<double, ZDIM, ZDIM, Eigen::RowMajor> ZZM;
  typedef Eigen::Matrix<double, ZDIM, DIM, Eigen::RowMajor> ZDM;
  typedef Eigen::Matrix<double, Eigen::Dynamic, EDIM, Eigen::RowMajor> XEM;
  //typedef Eigen::Matrix<double, EDIM, ZDIM, Eigen::RowMajor> EZM;
  typedef Eigen::Matrix<double, Eigen::Dynamic, 1> X1M;
  typedef Eigen::Matrix<double, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor> XXM;

  double in_hx[ZDIM] = {0};
  double in_H[ZDIM * DIM] = {0};
  double in_H_mod[EDIM * DIM] = {0};
  double delta_x[EDIM] = {0};
  double x_new[DIM] = {0};


  // state x, P
  Eigen::Matrix<double, ZDIM, 1> z(in_z);
  EEM P(in_P);
  ZZM pre_R(in_R);

  // functions from sympy
  h_fun(in_x, in_ea, in_hx);
  H_fun(in_x, in_ea, in_H);
  ZDM pre_H(in_H);

  // get y (y = z - hx)
  Eigen::Matrix<double, ZDIM, 1> pre_y(in_hx); pre_y = z - pre_y;
  X1M y; XXM H; XXM R;
  if (Hea_fun){
    typedef Eigen::Matrix<double, ZDIM, EADIM, Eigen::RowMajor> ZAM;
    double in_Hea[ZDIM * EADIM] = {0};
    Hea_fun(in_x, in_ea, in_Hea);
    ZAM Hea(in_Hea);
    XXM A = Hea.transpose().fullPivLu().kernel();


    y = A.transpose() * pre_y;
    H = A.transpose() * pre_H;
    R = A.transpose() * pre_R * A;
  } else {
    y = pre_y;
    H = pre_H;
    R = pre_R;
  }
  // get modified H
  H_mod_fun(in_x, in_H_mod);
  DEM H_mod(in_H_mod);
  XEM H_err = H * H_mod;

  // Do mahalobis distance test
  if (MAHA_TEST){
    XXM a = (H_err * P * H_err.transpose() + R).inverse();
    double maha_dist = y.transpose() * a * y;
    if (maha_dist > MAHA_THRESHOLD){
      R = 1.0e16 * R;
    }
  }

  // Outlier resilient weighting
  double weight = 1;//(1.5)/(1 + y.squaredNorm()/R.sum());

  // kalman gains and I_KH
  XXM S = ((H_err * P) * H_err.transpose()) + R/weight;
  XEM KT = S.fullPivLu().solve(H_err * P.transpose());
  //EZM K = KT.transpose(); TODO: WHY DOES THIS NOT COMPILE?
  //EZM K = S.fullPivLu().solve(H_err * P.transpose()).transpose();
  //std::cout << "Here is the matrix rot:\n" << K << std::endl;
  EEM I_KH = Eigen::Matrix<double, EDIM, EDIM>::Identity() - (KT.transpose() * H_err);

  // update state by injecting dx
  Eigen::Matrix<double, EDIM, 1> dx(delta_x);
  dx  = (KT.transpose() * y);
  memcpy(delta_x, dx.data(), EDIM * sizeof(double));
  err_fun(in_x, delta_x, x_new);
  Eigen::Matrix<double, DIM, 1> x(x_new);

  // update cov
  P = ((I_KH * P) * I_KH.transpose()) + ((KT.transpose() * R) * KT);

  // copy out state
  memcpy(in_x, x.data(), DIM * sizeof(double));
  memcpy(in_P, P.data(), EDIM * EDIM * sizeof(double));
  memcpy(in_z, y.data(), y.rows() * sizeof(double));
}




}
extern "C" {

void pose_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<3, 3, 0>(in_x, in_P, h_4, H_4, NULL, in_z, in_R, in_ea, MAHA_THRESH_4);
}
void pose_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<3, 3, 0>(in_x, in_P, h_10, H_10, NULL, in_z, in_R, in_ea, MAHA_THRESH_10);
}
void pose_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<3, 3, 0>(in_x, in_P, h_13, H_13, NULL, in_z, in_R, in_ea, MAHA_THRESH_13);
}
void pose_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<3, 3, 0>(in_x, in_P, h_14, H_14, NULL, in_z, in_R, in_ea, MAHA_THRESH_14);
}
void pose_err_fun(double *nom_x, double *delta_x, double *out_455516311871516666) {
  err_fun(nom_x, delta_x, out_455516311871516666);
}
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_4129318549302704896) {
  inv_err_fun(nom_x, true_x, out_4129318549302704896);
}
void pose_H_mod_fun(double *state, double *out_291361178655748996) {
  H_mod_fun(state, out_291361178655748996);
}
void pose_f_fun(double *state, double dt, double *out_6277713955818918611) {
  f_fun(state,  dt, out_6277713955818918611);
}
void pose_F_fun(double *state, double dt, double *out_3051886930390844105) {
  F_fun(state,  dt, out_3051886930390844105);
}
void pose_h_4(double *state, double *unused, double *out_1179958653059836279) {
  h_4(state, unused, out_1179958653059836279);
}
void pose_H_4(double *state, double *unused, double *out_3634206011302561399) {
  H_4(state, unused, out_3634206011302561399);
}
void pose_h_10(double *state, double *unused, double *out_7917951398739470562) {
  h_10(state, unused, out_7917951398739470562);
}
void pose_H_10(double *state, double *unused, double *out_5574544512634486876) {
  H_10(state, unused, out_5574544512634486876);
}
void pose_h_13(double *state, double *unused, double *out_7282516462007542478) {
  h_13(state, unused, out_7282516462007542478);
}
void pose_H_13(double *state, double *unused, double *out_6846479836634894200) {
  H_13(state, unused, out_6846479836634894200);
}
void pose_h_14(double *state, double *unused, double *out_7084974374367104635) {
  h_14(state, unused, out_7084974374367104635);
}
void pose_H_14(double *state, double *unused, double *out_551417579007189103) {
  H_14(state, unused, out_551417579007189103);
}
void pose_predict(double *in_x, double *in_P, double *in_Q, double dt) {
  predict(in_x, in_P, in_Q, dt);
}
}

const EKF pose = {
  .name = "pose",
  .kinds = { 4, 10, 13, 14 },
  .feature_kinds = {  },
  .f_fun = pose_f_fun,
  .F_fun = pose_F_fun,
  .err_fun = pose_err_fun,
  .inv_err_fun = pose_inv_err_fun,
  .H_mod_fun = pose_H_mod_fun,
  .predict = pose_predict,
  .hs = {
    { 4, pose_h_4 },
    { 10, pose_h_10 },
    { 13, pose_h_13 },
    { 14, pose_h_14 },
  },
  .Hs = {
    { 4, pose_H_4 },
    { 10, pose_H_10 },
    { 13, pose_H_13 },
    { 14, pose_H_14 },
  },
  .updates = {
    { 4, pose_update_4 },
    { 10, pose_update_10 },
    { 13, pose_update_13 },
    { 14, pose_update_14 },
  },
  .Hes = {
  },
  .sets = {
  },
  .extra_routines = {
  },
};

ekf_lib_init(pose)
