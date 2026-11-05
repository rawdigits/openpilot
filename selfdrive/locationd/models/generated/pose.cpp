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
 *                      Code generated with SymPy 1.13.2                      *
 *                                                                            *
 *              See http://www.sympy.org/ for more information.               *
 *                                                                            *
 *                         This file is part of 'ekf'                         *
 ******************************************************************************/
void err_fun(double *nom_x, double *delta_x, double *out_3394550637581824468) {
   out_3394550637581824468[0] = delta_x[0] + nom_x[0];
   out_3394550637581824468[1] = delta_x[1] + nom_x[1];
   out_3394550637581824468[2] = delta_x[2] + nom_x[2];
   out_3394550637581824468[3] = delta_x[3] + nom_x[3];
   out_3394550637581824468[4] = delta_x[4] + nom_x[4];
   out_3394550637581824468[5] = delta_x[5] + nom_x[5];
   out_3394550637581824468[6] = delta_x[6] + nom_x[6];
   out_3394550637581824468[7] = delta_x[7] + nom_x[7];
   out_3394550637581824468[8] = delta_x[8] + nom_x[8];
   out_3394550637581824468[9] = delta_x[9] + nom_x[9];
   out_3394550637581824468[10] = delta_x[10] + nom_x[10];
   out_3394550637581824468[11] = delta_x[11] + nom_x[11];
   out_3394550637581824468[12] = delta_x[12] + nom_x[12];
   out_3394550637581824468[13] = delta_x[13] + nom_x[13];
   out_3394550637581824468[14] = delta_x[14] + nom_x[14];
   out_3394550637581824468[15] = delta_x[15] + nom_x[15];
   out_3394550637581824468[16] = delta_x[16] + nom_x[16];
   out_3394550637581824468[17] = delta_x[17] + nom_x[17];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_774672115471856853) {
   out_774672115471856853[0] = -nom_x[0] + true_x[0];
   out_774672115471856853[1] = -nom_x[1] + true_x[1];
   out_774672115471856853[2] = -nom_x[2] + true_x[2];
   out_774672115471856853[3] = -nom_x[3] + true_x[3];
   out_774672115471856853[4] = -nom_x[4] + true_x[4];
   out_774672115471856853[5] = -nom_x[5] + true_x[5];
   out_774672115471856853[6] = -nom_x[6] + true_x[6];
   out_774672115471856853[7] = -nom_x[7] + true_x[7];
   out_774672115471856853[8] = -nom_x[8] + true_x[8];
   out_774672115471856853[9] = -nom_x[9] + true_x[9];
   out_774672115471856853[10] = -nom_x[10] + true_x[10];
   out_774672115471856853[11] = -nom_x[11] + true_x[11];
   out_774672115471856853[12] = -nom_x[12] + true_x[12];
   out_774672115471856853[13] = -nom_x[13] + true_x[13];
   out_774672115471856853[14] = -nom_x[14] + true_x[14];
   out_774672115471856853[15] = -nom_x[15] + true_x[15];
   out_774672115471856853[16] = -nom_x[16] + true_x[16];
   out_774672115471856853[17] = -nom_x[17] + true_x[17];
}
void H_mod_fun(double *state, double *out_7710816715974909147) {
   out_7710816715974909147[0] = 1.0;
   out_7710816715974909147[1] = 0.0;
   out_7710816715974909147[2] = 0.0;
   out_7710816715974909147[3] = 0.0;
   out_7710816715974909147[4] = 0.0;
   out_7710816715974909147[5] = 0.0;
   out_7710816715974909147[6] = 0.0;
   out_7710816715974909147[7] = 0.0;
   out_7710816715974909147[8] = 0.0;
   out_7710816715974909147[9] = 0.0;
   out_7710816715974909147[10] = 0.0;
   out_7710816715974909147[11] = 0.0;
   out_7710816715974909147[12] = 0.0;
   out_7710816715974909147[13] = 0.0;
   out_7710816715974909147[14] = 0.0;
   out_7710816715974909147[15] = 0.0;
   out_7710816715974909147[16] = 0.0;
   out_7710816715974909147[17] = 0.0;
   out_7710816715974909147[18] = 0.0;
   out_7710816715974909147[19] = 1.0;
   out_7710816715974909147[20] = 0.0;
   out_7710816715974909147[21] = 0.0;
   out_7710816715974909147[22] = 0.0;
   out_7710816715974909147[23] = 0.0;
   out_7710816715974909147[24] = 0.0;
   out_7710816715974909147[25] = 0.0;
   out_7710816715974909147[26] = 0.0;
   out_7710816715974909147[27] = 0.0;
   out_7710816715974909147[28] = 0.0;
   out_7710816715974909147[29] = 0.0;
   out_7710816715974909147[30] = 0.0;
   out_7710816715974909147[31] = 0.0;
   out_7710816715974909147[32] = 0.0;
   out_7710816715974909147[33] = 0.0;
   out_7710816715974909147[34] = 0.0;
   out_7710816715974909147[35] = 0.0;
   out_7710816715974909147[36] = 0.0;
   out_7710816715974909147[37] = 0.0;
   out_7710816715974909147[38] = 1.0;
   out_7710816715974909147[39] = 0.0;
   out_7710816715974909147[40] = 0.0;
   out_7710816715974909147[41] = 0.0;
   out_7710816715974909147[42] = 0.0;
   out_7710816715974909147[43] = 0.0;
   out_7710816715974909147[44] = 0.0;
   out_7710816715974909147[45] = 0.0;
   out_7710816715974909147[46] = 0.0;
   out_7710816715974909147[47] = 0.0;
   out_7710816715974909147[48] = 0.0;
   out_7710816715974909147[49] = 0.0;
   out_7710816715974909147[50] = 0.0;
   out_7710816715974909147[51] = 0.0;
   out_7710816715974909147[52] = 0.0;
   out_7710816715974909147[53] = 0.0;
   out_7710816715974909147[54] = 0.0;
   out_7710816715974909147[55] = 0.0;
   out_7710816715974909147[56] = 0.0;
   out_7710816715974909147[57] = 1.0;
   out_7710816715974909147[58] = 0.0;
   out_7710816715974909147[59] = 0.0;
   out_7710816715974909147[60] = 0.0;
   out_7710816715974909147[61] = 0.0;
   out_7710816715974909147[62] = 0.0;
   out_7710816715974909147[63] = 0.0;
   out_7710816715974909147[64] = 0.0;
   out_7710816715974909147[65] = 0.0;
   out_7710816715974909147[66] = 0.0;
   out_7710816715974909147[67] = 0.0;
   out_7710816715974909147[68] = 0.0;
   out_7710816715974909147[69] = 0.0;
   out_7710816715974909147[70] = 0.0;
   out_7710816715974909147[71] = 0.0;
   out_7710816715974909147[72] = 0.0;
   out_7710816715974909147[73] = 0.0;
   out_7710816715974909147[74] = 0.0;
   out_7710816715974909147[75] = 0.0;
   out_7710816715974909147[76] = 1.0;
   out_7710816715974909147[77] = 0.0;
   out_7710816715974909147[78] = 0.0;
   out_7710816715974909147[79] = 0.0;
   out_7710816715974909147[80] = 0.0;
   out_7710816715974909147[81] = 0.0;
   out_7710816715974909147[82] = 0.0;
   out_7710816715974909147[83] = 0.0;
   out_7710816715974909147[84] = 0.0;
   out_7710816715974909147[85] = 0.0;
   out_7710816715974909147[86] = 0.0;
   out_7710816715974909147[87] = 0.0;
   out_7710816715974909147[88] = 0.0;
   out_7710816715974909147[89] = 0.0;
   out_7710816715974909147[90] = 0.0;
   out_7710816715974909147[91] = 0.0;
   out_7710816715974909147[92] = 0.0;
   out_7710816715974909147[93] = 0.0;
   out_7710816715974909147[94] = 0.0;
   out_7710816715974909147[95] = 1.0;
   out_7710816715974909147[96] = 0.0;
   out_7710816715974909147[97] = 0.0;
   out_7710816715974909147[98] = 0.0;
   out_7710816715974909147[99] = 0.0;
   out_7710816715974909147[100] = 0.0;
   out_7710816715974909147[101] = 0.0;
   out_7710816715974909147[102] = 0.0;
   out_7710816715974909147[103] = 0.0;
   out_7710816715974909147[104] = 0.0;
   out_7710816715974909147[105] = 0.0;
   out_7710816715974909147[106] = 0.0;
   out_7710816715974909147[107] = 0.0;
   out_7710816715974909147[108] = 0.0;
   out_7710816715974909147[109] = 0.0;
   out_7710816715974909147[110] = 0.0;
   out_7710816715974909147[111] = 0.0;
   out_7710816715974909147[112] = 0.0;
   out_7710816715974909147[113] = 0.0;
   out_7710816715974909147[114] = 1.0;
   out_7710816715974909147[115] = 0.0;
   out_7710816715974909147[116] = 0.0;
   out_7710816715974909147[117] = 0.0;
   out_7710816715974909147[118] = 0.0;
   out_7710816715974909147[119] = 0.0;
   out_7710816715974909147[120] = 0.0;
   out_7710816715974909147[121] = 0.0;
   out_7710816715974909147[122] = 0.0;
   out_7710816715974909147[123] = 0.0;
   out_7710816715974909147[124] = 0.0;
   out_7710816715974909147[125] = 0.0;
   out_7710816715974909147[126] = 0.0;
   out_7710816715974909147[127] = 0.0;
   out_7710816715974909147[128] = 0.0;
   out_7710816715974909147[129] = 0.0;
   out_7710816715974909147[130] = 0.0;
   out_7710816715974909147[131] = 0.0;
   out_7710816715974909147[132] = 0.0;
   out_7710816715974909147[133] = 1.0;
   out_7710816715974909147[134] = 0.0;
   out_7710816715974909147[135] = 0.0;
   out_7710816715974909147[136] = 0.0;
   out_7710816715974909147[137] = 0.0;
   out_7710816715974909147[138] = 0.0;
   out_7710816715974909147[139] = 0.0;
   out_7710816715974909147[140] = 0.0;
   out_7710816715974909147[141] = 0.0;
   out_7710816715974909147[142] = 0.0;
   out_7710816715974909147[143] = 0.0;
   out_7710816715974909147[144] = 0.0;
   out_7710816715974909147[145] = 0.0;
   out_7710816715974909147[146] = 0.0;
   out_7710816715974909147[147] = 0.0;
   out_7710816715974909147[148] = 0.0;
   out_7710816715974909147[149] = 0.0;
   out_7710816715974909147[150] = 0.0;
   out_7710816715974909147[151] = 0.0;
   out_7710816715974909147[152] = 1.0;
   out_7710816715974909147[153] = 0.0;
   out_7710816715974909147[154] = 0.0;
   out_7710816715974909147[155] = 0.0;
   out_7710816715974909147[156] = 0.0;
   out_7710816715974909147[157] = 0.0;
   out_7710816715974909147[158] = 0.0;
   out_7710816715974909147[159] = 0.0;
   out_7710816715974909147[160] = 0.0;
   out_7710816715974909147[161] = 0.0;
   out_7710816715974909147[162] = 0.0;
   out_7710816715974909147[163] = 0.0;
   out_7710816715974909147[164] = 0.0;
   out_7710816715974909147[165] = 0.0;
   out_7710816715974909147[166] = 0.0;
   out_7710816715974909147[167] = 0.0;
   out_7710816715974909147[168] = 0.0;
   out_7710816715974909147[169] = 0.0;
   out_7710816715974909147[170] = 0.0;
   out_7710816715974909147[171] = 1.0;
   out_7710816715974909147[172] = 0.0;
   out_7710816715974909147[173] = 0.0;
   out_7710816715974909147[174] = 0.0;
   out_7710816715974909147[175] = 0.0;
   out_7710816715974909147[176] = 0.0;
   out_7710816715974909147[177] = 0.0;
   out_7710816715974909147[178] = 0.0;
   out_7710816715974909147[179] = 0.0;
   out_7710816715974909147[180] = 0.0;
   out_7710816715974909147[181] = 0.0;
   out_7710816715974909147[182] = 0.0;
   out_7710816715974909147[183] = 0.0;
   out_7710816715974909147[184] = 0.0;
   out_7710816715974909147[185] = 0.0;
   out_7710816715974909147[186] = 0.0;
   out_7710816715974909147[187] = 0.0;
   out_7710816715974909147[188] = 0.0;
   out_7710816715974909147[189] = 0.0;
   out_7710816715974909147[190] = 1.0;
   out_7710816715974909147[191] = 0.0;
   out_7710816715974909147[192] = 0.0;
   out_7710816715974909147[193] = 0.0;
   out_7710816715974909147[194] = 0.0;
   out_7710816715974909147[195] = 0.0;
   out_7710816715974909147[196] = 0.0;
   out_7710816715974909147[197] = 0.0;
   out_7710816715974909147[198] = 0.0;
   out_7710816715974909147[199] = 0.0;
   out_7710816715974909147[200] = 0.0;
   out_7710816715974909147[201] = 0.0;
   out_7710816715974909147[202] = 0.0;
   out_7710816715974909147[203] = 0.0;
   out_7710816715974909147[204] = 0.0;
   out_7710816715974909147[205] = 0.0;
   out_7710816715974909147[206] = 0.0;
   out_7710816715974909147[207] = 0.0;
   out_7710816715974909147[208] = 0.0;
   out_7710816715974909147[209] = 1.0;
   out_7710816715974909147[210] = 0.0;
   out_7710816715974909147[211] = 0.0;
   out_7710816715974909147[212] = 0.0;
   out_7710816715974909147[213] = 0.0;
   out_7710816715974909147[214] = 0.0;
   out_7710816715974909147[215] = 0.0;
   out_7710816715974909147[216] = 0.0;
   out_7710816715974909147[217] = 0.0;
   out_7710816715974909147[218] = 0.0;
   out_7710816715974909147[219] = 0.0;
   out_7710816715974909147[220] = 0.0;
   out_7710816715974909147[221] = 0.0;
   out_7710816715974909147[222] = 0.0;
   out_7710816715974909147[223] = 0.0;
   out_7710816715974909147[224] = 0.0;
   out_7710816715974909147[225] = 0.0;
   out_7710816715974909147[226] = 0.0;
   out_7710816715974909147[227] = 0.0;
   out_7710816715974909147[228] = 1.0;
   out_7710816715974909147[229] = 0.0;
   out_7710816715974909147[230] = 0.0;
   out_7710816715974909147[231] = 0.0;
   out_7710816715974909147[232] = 0.0;
   out_7710816715974909147[233] = 0.0;
   out_7710816715974909147[234] = 0.0;
   out_7710816715974909147[235] = 0.0;
   out_7710816715974909147[236] = 0.0;
   out_7710816715974909147[237] = 0.0;
   out_7710816715974909147[238] = 0.0;
   out_7710816715974909147[239] = 0.0;
   out_7710816715974909147[240] = 0.0;
   out_7710816715974909147[241] = 0.0;
   out_7710816715974909147[242] = 0.0;
   out_7710816715974909147[243] = 0.0;
   out_7710816715974909147[244] = 0.0;
   out_7710816715974909147[245] = 0.0;
   out_7710816715974909147[246] = 0.0;
   out_7710816715974909147[247] = 1.0;
   out_7710816715974909147[248] = 0.0;
   out_7710816715974909147[249] = 0.0;
   out_7710816715974909147[250] = 0.0;
   out_7710816715974909147[251] = 0.0;
   out_7710816715974909147[252] = 0.0;
   out_7710816715974909147[253] = 0.0;
   out_7710816715974909147[254] = 0.0;
   out_7710816715974909147[255] = 0.0;
   out_7710816715974909147[256] = 0.0;
   out_7710816715974909147[257] = 0.0;
   out_7710816715974909147[258] = 0.0;
   out_7710816715974909147[259] = 0.0;
   out_7710816715974909147[260] = 0.0;
   out_7710816715974909147[261] = 0.0;
   out_7710816715974909147[262] = 0.0;
   out_7710816715974909147[263] = 0.0;
   out_7710816715974909147[264] = 0.0;
   out_7710816715974909147[265] = 0.0;
   out_7710816715974909147[266] = 1.0;
   out_7710816715974909147[267] = 0.0;
   out_7710816715974909147[268] = 0.0;
   out_7710816715974909147[269] = 0.0;
   out_7710816715974909147[270] = 0.0;
   out_7710816715974909147[271] = 0.0;
   out_7710816715974909147[272] = 0.0;
   out_7710816715974909147[273] = 0.0;
   out_7710816715974909147[274] = 0.0;
   out_7710816715974909147[275] = 0.0;
   out_7710816715974909147[276] = 0.0;
   out_7710816715974909147[277] = 0.0;
   out_7710816715974909147[278] = 0.0;
   out_7710816715974909147[279] = 0.0;
   out_7710816715974909147[280] = 0.0;
   out_7710816715974909147[281] = 0.0;
   out_7710816715974909147[282] = 0.0;
   out_7710816715974909147[283] = 0.0;
   out_7710816715974909147[284] = 0.0;
   out_7710816715974909147[285] = 1.0;
   out_7710816715974909147[286] = 0.0;
   out_7710816715974909147[287] = 0.0;
   out_7710816715974909147[288] = 0.0;
   out_7710816715974909147[289] = 0.0;
   out_7710816715974909147[290] = 0.0;
   out_7710816715974909147[291] = 0.0;
   out_7710816715974909147[292] = 0.0;
   out_7710816715974909147[293] = 0.0;
   out_7710816715974909147[294] = 0.0;
   out_7710816715974909147[295] = 0.0;
   out_7710816715974909147[296] = 0.0;
   out_7710816715974909147[297] = 0.0;
   out_7710816715974909147[298] = 0.0;
   out_7710816715974909147[299] = 0.0;
   out_7710816715974909147[300] = 0.0;
   out_7710816715974909147[301] = 0.0;
   out_7710816715974909147[302] = 0.0;
   out_7710816715974909147[303] = 0.0;
   out_7710816715974909147[304] = 1.0;
   out_7710816715974909147[305] = 0.0;
   out_7710816715974909147[306] = 0.0;
   out_7710816715974909147[307] = 0.0;
   out_7710816715974909147[308] = 0.0;
   out_7710816715974909147[309] = 0.0;
   out_7710816715974909147[310] = 0.0;
   out_7710816715974909147[311] = 0.0;
   out_7710816715974909147[312] = 0.0;
   out_7710816715974909147[313] = 0.0;
   out_7710816715974909147[314] = 0.0;
   out_7710816715974909147[315] = 0.0;
   out_7710816715974909147[316] = 0.0;
   out_7710816715974909147[317] = 0.0;
   out_7710816715974909147[318] = 0.0;
   out_7710816715974909147[319] = 0.0;
   out_7710816715974909147[320] = 0.0;
   out_7710816715974909147[321] = 0.0;
   out_7710816715974909147[322] = 0.0;
   out_7710816715974909147[323] = 1.0;
}
void f_fun(double *state, double dt, double *out_5487839870694824154) {
   out_5487839870694824154[0] = atan2((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), -(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]));
   out_5487839870694824154[1] = asin(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]));
   out_5487839870694824154[2] = atan2(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), -(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]));
   out_5487839870694824154[3] = dt*state[12] + state[3];
   out_5487839870694824154[4] = dt*state[13] + state[4];
   out_5487839870694824154[5] = dt*state[14] + state[5];
   out_5487839870694824154[6] = state[6];
   out_5487839870694824154[7] = state[7];
   out_5487839870694824154[8] = state[8];
   out_5487839870694824154[9] = state[9];
   out_5487839870694824154[10] = state[10];
   out_5487839870694824154[11] = state[11];
   out_5487839870694824154[12] = state[12];
   out_5487839870694824154[13] = state[13];
   out_5487839870694824154[14] = state[14];
   out_5487839870694824154[15] = state[15];
   out_5487839870694824154[16] = state[16];
   out_5487839870694824154[17] = state[17];
}
void F_fun(double *state, double dt, double *out_5336850415855987983) {
   out_5336850415855987983[0] = ((-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*cos(state[0])*cos(state[1]) - sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*cos(state[0])*cos(state[1]) - sin(dt*state[6])*sin(state[0])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_5336850415855987983[1] = ((-sin(dt*state[6])*sin(dt*state[8]) - sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*cos(state[1]) - (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*sin(state[1]) - sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(state[0]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*sin(state[1]) + (-sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) + sin(dt*state[8])*cos(dt*state[6]))*cos(state[1]) - sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(state[0]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_5336850415855987983[2] = 0;
   out_5336850415855987983[3] = 0;
   out_5336850415855987983[4] = 0;
   out_5336850415855987983[5] = 0;
   out_5336850415855987983[6] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(dt*cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) - dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_5336850415855987983[7] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*sin(dt*state[7])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[6])*sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) - dt*sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[7])*cos(dt*state[6])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[8])*sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]) - dt*sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_5336850415855987983[8] = ((dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((dt*sin(dt*state[6])*sin(dt*state[8]) + dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_5336850415855987983[9] = 0;
   out_5336850415855987983[10] = 0;
   out_5336850415855987983[11] = 0;
   out_5336850415855987983[12] = 0;
   out_5336850415855987983[13] = 0;
   out_5336850415855987983[14] = 0;
   out_5336850415855987983[15] = 0;
   out_5336850415855987983[16] = 0;
   out_5336850415855987983[17] = 0;
   out_5336850415855987983[18] = (-sin(dt*state[7])*sin(state[0])*cos(state[1]) - sin(dt*state[8])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_5336850415855987983[19] = (-sin(dt*state[7])*sin(state[1])*cos(state[0]) + sin(dt*state[8])*sin(state[0])*sin(state[1])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_5336850415855987983[20] = 0;
   out_5336850415855987983[21] = 0;
   out_5336850415855987983[22] = 0;
   out_5336850415855987983[23] = 0;
   out_5336850415855987983[24] = 0;
   out_5336850415855987983[25] = (dt*sin(dt*state[7])*sin(dt*state[8])*sin(state[0])*cos(state[1]) - dt*sin(dt*state[7])*sin(state[1])*cos(dt*state[8]) + dt*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_5336850415855987983[26] = (-dt*sin(dt*state[8])*sin(state[1])*cos(dt*state[7]) - dt*sin(state[0])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_5336850415855987983[27] = 0;
   out_5336850415855987983[28] = 0;
   out_5336850415855987983[29] = 0;
   out_5336850415855987983[30] = 0;
   out_5336850415855987983[31] = 0;
   out_5336850415855987983[32] = 0;
   out_5336850415855987983[33] = 0;
   out_5336850415855987983[34] = 0;
   out_5336850415855987983[35] = 0;
   out_5336850415855987983[36] = ((sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_5336850415855987983[37] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-sin(dt*state[7])*sin(state[2])*cos(state[0])*cos(state[1]) + sin(dt*state[8])*sin(state[0])*sin(state[2])*cos(dt*state[7])*cos(state[1]) - sin(state[1])*sin(state[2])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(-sin(dt*state[7])*cos(state[0])*cos(state[1])*cos(state[2]) + sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1])*cos(state[2]) - sin(state[1])*cos(dt*state[7])*cos(dt*state[8])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_5336850415855987983[38] = ((-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (-sin(state[0])*sin(state[1])*sin(state[2]) - cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_5336850415855987983[39] = 0;
   out_5336850415855987983[40] = 0;
   out_5336850415855987983[41] = 0;
   out_5336850415855987983[42] = 0;
   out_5336850415855987983[43] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(dt*(sin(state[0])*cos(state[2]) - sin(state[1])*sin(state[2])*cos(state[0]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*sin(state[2])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(dt*(-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_5336850415855987983[44] = (dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*sin(state[2])*cos(dt*state[7])*cos(state[1]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + (dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[7])*cos(state[1])*cos(state[2]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_5336850415855987983[45] = 0;
   out_5336850415855987983[46] = 0;
   out_5336850415855987983[47] = 0;
   out_5336850415855987983[48] = 0;
   out_5336850415855987983[49] = 0;
   out_5336850415855987983[50] = 0;
   out_5336850415855987983[51] = 0;
   out_5336850415855987983[52] = 0;
   out_5336850415855987983[53] = 0;
   out_5336850415855987983[54] = 0;
   out_5336850415855987983[55] = 0;
   out_5336850415855987983[56] = 0;
   out_5336850415855987983[57] = 1;
   out_5336850415855987983[58] = 0;
   out_5336850415855987983[59] = 0;
   out_5336850415855987983[60] = 0;
   out_5336850415855987983[61] = 0;
   out_5336850415855987983[62] = 0;
   out_5336850415855987983[63] = 0;
   out_5336850415855987983[64] = 0;
   out_5336850415855987983[65] = 0;
   out_5336850415855987983[66] = dt;
   out_5336850415855987983[67] = 0;
   out_5336850415855987983[68] = 0;
   out_5336850415855987983[69] = 0;
   out_5336850415855987983[70] = 0;
   out_5336850415855987983[71] = 0;
   out_5336850415855987983[72] = 0;
   out_5336850415855987983[73] = 0;
   out_5336850415855987983[74] = 0;
   out_5336850415855987983[75] = 0;
   out_5336850415855987983[76] = 1;
   out_5336850415855987983[77] = 0;
   out_5336850415855987983[78] = 0;
   out_5336850415855987983[79] = 0;
   out_5336850415855987983[80] = 0;
   out_5336850415855987983[81] = 0;
   out_5336850415855987983[82] = 0;
   out_5336850415855987983[83] = 0;
   out_5336850415855987983[84] = 0;
   out_5336850415855987983[85] = dt;
   out_5336850415855987983[86] = 0;
   out_5336850415855987983[87] = 0;
   out_5336850415855987983[88] = 0;
   out_5336850415855987983[89] = 0;
   out_5336850415855987983[90] = 0;
   out_5336850415855987983[91] = 0;
   out_5336850415855987983[92] = 0;
   out_5336850415855987983[93] = 0;
   out_5336850415855987983[94] = 0;
   out_5336850415855987983[95] = 1;
   out_5336850415855987983[96] = 0;
   out_5336850415855987983[97] = 0;
   out_5336850415855987983[98] = 0;
   out_5336850415855987983[99] = 0;
   out_5336850415855987983[100] = 0;
   out_5336850415855987983[101] = 0;
   out_5336850415855987983[102] = 0;
   out_5336850415855987983[103] = 0;
   out_5336850415855987983[104] = dt;
   out_5336850415855987983[105] = 0;
   out_5336850415855987983[106] = 0;
   out_5336850415855987983[107] = 0;
   out_5336850415855987983[108] = 0;
   out_5336850415855987983[109] = 0;
   out_5336850415855987983[110] = 0;
   out_5336850415855987983[111] = 0;
   out_5336850415855987983[112] = 0;
   out_5336850415855987983[113] = 0;
   out_5336850415855987983[114] = 1;
   out_5336850415855987983[115] = 0;
   out_5336850415855987983[116] = 0;
   out_5336850415855987983[117] = 0;
   out_5336850415855987983[118] = 0;
   out_5336850415855987983[119] = 0;
   out_5336850415855987983[120] = 0;
   out_5336850415855987983[121] = 0;
   out_5336850415855987983[122] = 0;
   out_5336850415855987983[123] = 0;
   out_5336850415855987983[124] = 0;
   out_5336850415855987983[125] = 0;
   out_5336850415855987983[126] = 0;
   out_5336850415855987983[127] = 0;
   out_5336850415855987983[128] = 0;
   out_5336850415855987983[129] = 0;
   out_5336850415855987983[130] = 0;
   out_5336850415855987983[131] = 0;
   out_5336850415855987983[132] = 0;
   out_5336850415855987983[133] = 1;
   out_5336850415855987983[134] = 0;
   out_5336850415855987983[135] = 0;
   out_5336850415855987983[136] = 0;
   out_5336850415855987983[137] = 0;
   out_5336850415855987983[138] = 0;
   out_5336850415855987983[139] = 0;
   out_5336850415855987983[140] = 0;
   out_5336850415855987983[141] = 0;
   out_5336850415855987983[142] = 0;
   out_5336850415855987983[143] = 0;
   out_5336850415855987983[144] = 0;
   out_5336850415855987983[145] = 0;
   out_5336850415855987983[146] = 0;
   out_5336850415855987983[147] = 0;
   out_5336850415855987983[148] = 0;
   out_5336850415855987983[149] = 0;
   out_5336850415855987983[150] = 0;
   out_5336850415855987983[151] = 0;
   out_5336850415855987983[152] = 1;
   out_5336850415855987983[153] = 0;
   out_5336850415855987983[154] = 0;
   out_5336850415855987983[155] = 0;
   out_5336850415855987983[156] = 0;
   out_5336850415855987983[157] = 0;
   out_5336850415855987983[158] = 0;
   out_5336850415855987983[159] = 0;
   out_5336850415855987983[160] = 0;
   out_5336850415855987983[161] = 0;
   out_5336850415855987983[162] = 0;
   out_5336850415855987983[163] = 0;
   out_5336850415855987983[164] = 0;
   out_5336850415855987983[165] = 0;
   out_5336850415855987983[166] = 0;
   out_5336850415855987983[167] = 0;
   out_5336850415855987983[168] = 0;
   out_5336850415855987983[169] = 0;
   out_5336850415855987983[170] = 0;
   out_5336850415855987983[171] = 1;
   out_5336850415855987983[172] = 0;
   out_5336850415855987983[173] = 0;
   out_5336850415855987983[174] = 0;
   out_5336850415855987983[175] = 0;
   out_5336850415855987983[176] = 0;
   out_5336850415855987983[177] = 0;
   out_5336850415855987983[178] = 0;
   out_5336850415855987983[179] = 0;
   out_5336850415855987983[180] = 0;
   out_5336850415855987983[181] = 0;
   out_5336850415855987983[182] = 0;
   out_5336850415855987983[183] = 0;
   out_5336850415855987983[184] = 0;
   out_5336850415855987983[185] = 0;
   out_5336850415855987983[186] = 0;
   out_5336850415855987983[187] = 0;
   out_5336850415855987983[188] = 0;
   out_5336850415855987983[189] = 0;
   out_5336850415855987983[190] = 1;
   out_5336850415855987983[191] = 0;
   out_5336850415855987983[192] = 0;
   out_5336850415855987983[193] = 0;
   out_5336850415855987983[194] = 0;
   out_5336850415855987983[195] = 0;
   out_5336850415855987983[196] = 0;
   out_5336850415855987983[197] = 0;
   out_5336850415855987983[198] = 0;
   out_5336850415855987983[199] = 0;
   out_5336850415855987983[200] = 0;
   out_5336850415855987983[201] = 0;
   out_5336850415855987983[202] = 0;
   out_5336850415855987983[203] = 0;
   out_5336850415855987983[204] = 0;
   out_5336850415855987983[205] = 0;
   out_5336850415855987983[206] = 0;
   out_5336850415855987983[207] = 0;
   out_5336850415855987983[208] = 0;
   out_5336850415855987983[209] = 1;
   out_5336850415855987983[210] = 0;
   out_5336850415855987983[211] = 0;
   out_5336850415855987983[212] = 0;
   out_5336850415855987983[213] = 0;
   out_5336850415855987983[214] = 0;
   out_5336850415855987983[215] = 0;
   out_5336850415855987983[216] = 0;
   out_5336850415855987983[217] = 0;
   out_5336850415855987983[218] = 0;
   out_5336850415855987983[219] = 0;
   out_5336850415855987983[220] = 0;
   out_5336850415855987983[221] = 0;
   out_5336850415855987983[222] = 0;
   out_5336850415855987983[223] = 0;
   out_5336850415855987983[224] = 0;
   out_5336850415855987983[225] = 0;
   out_5336850415855987983[226] = 0;
   out_5336850415855987983[227] = 0;
   out_5336850415855987983[228] = 1;
   out_5336850415855987983[229] = 0;
   out_5336850415855987983[230] = 0;
   out_5336850415855987983[231] = 0;
   out_5336850415855987983[232] = 0;
   out_5336850415855987983[233] = 0;
   out_5336850415855987983[234] = 0;
   out_5336850415855987983[235] = 0;
   out_5336850415855987983[236] = 0;
   out_5336850415855987983[237] = 0;
   out_5336850415855987983[238] = 0;
   out_5336850415855987983[239] = 0;
   out_5336850415855987983[240] = 0;
   out_5336850415855987983[241] = 0;
   out_5336850415855987983[242] = 0;
   out_5336850415855987983[243] = 0;
   out_5336850415855987983[244] = 0;
   out_5336850415855987983[245] = 0;
   out_5336850415855987983[246] = 0;
   out_5336850415855987983[247] = 1;
   out_5336850415855987983[248] = 0;
   out_5336850415855987983[249] = 0;
   out_5336850415855987983[250] = 0;
   out_5336850415855987983[251] = 0;
   out_5336850415855987983[252] = 0;
   out_5336850415855987983[253] = 0;
   out_5336850415855987983[254] = 0;
   out_5336850415855987983[255] = 0;
   out_5336850415855987983[256] = 0;
   out_5336850415855987983[257] = 0;
   out_5336850415855987983[258] = 0;
   out_5336850415855987983[259] = 0;
   out_5336850415855987983[260] = 0;
   out_5336850415855987983[261] = 0;
   out_5336850415855987983[262] = 0;
   out_5336850415855987983[263] = 0;
   out_5336850415855987983[264] = 0;
   out_5336850415855987983[265] = 0;
   out_5336850415855987983[266] = 1;
   out_5336850415855987983[267] = 0;
   out_5336850415855987983[268] = 0;
   out_5336850415855987983[269] = 0;
   out_5336850415855987983[270] = 0;
   out_5336850415855987983[271] = 0;
   out_5336850415855987983[272] = 0;
   out_5336850415855987983[273] = 0;
   out_5336850415855987983[274] = 0;
   out_5336850415855987983[275] = 0;
   out_5336850415855987983[276] = 0;
   out_5336850415855987983[277] = 0;
   out_5336850415855987983[278] = 0;
   out_5336850415855987983[279] = 0;
   out_5336850415855987983[280] = 0;
   out_5336850415855987983[281] = 0;
   out_5336850415855987983[282] = 0;
   out_5336850415855987983[283] = 0;
   out_5336850415855987983[284] = 0;
   out_5336850415855987983[285] = 1;
   out_5336850415855987983[286] = 0;
   out_5336850415855987983[287] = 0;
   out_5336850415855987983[288] = 0;
   out_5336850415855987983[289] = 0;
   out_5336850415855987983[290] = 0;
   out_5336850415855987983[291] = 0;
   out_5336850415855987983[292] = 0;
   out_5336850415855987983[293] = 0;
   out_5336850415855987983[294] = 0;
   out_5336850415855987983[295] = 0;
   out_5336850415855987983[296] = 0;
   out_5336850415855987983[297] = 0;
   out_5336850415855987983[298] = 0;
   out_5336850415855987983[299] = 0;
   out_5336850415855987983[300] = 0;
   out_5336850415855987983[301] = 0;
   out_5336850415855987983[302] = 0;
   out_5336850415855987983[303] = 0;
   out_5336850415855987983[304] = 1;
   out_5336850415855987983[305] = 0;
   out_5336850415855987983[306] = 0;
   out_5336850415855987983[307] = 0;
   out_5336850415855987983[308] = 0;
   out_5336850415855987983[309] = 0;
   out_5336850415855987983[310] = 0;
   out_5336850415855987983[311] = 0;
   out_5336850415855987983[312] = 0;
   out_5336850415855987983[313] = 0;
   out_5336850415855987983[314] = 0;
   out_5336850415855987983[315] = 0;
   out_5336850415855987983[316] = 0;
   out_5336850415855987983[317] = 0;
   out_5336850415855987983[318] = 0;
   out_5336850415855987983[319] = 0;
   out_5336850415855987983[320] = 0;
   out_5336850415855987983[321] = 0;
   out_5336850415855987983[322] = 0;
   out_5336850415855987983[323] = 1;
}
void h_4(double *state, double *unused, double *out_7487667227305404692) {
   out_7487667227305404692[0] = state[6] + state[9];
   out_7487667227305404692[1] = state[7] + state[10];
   out_7487667227305404692[2] = state[8] + state[11];
}
void H_4(double *state, double *unused, double *out_3939009506131001575) {
   out_3939009506131001575[0] = 0;
   out_3939009506131001575[1] = 0;
   out_3939009506131001575[2] = 0;
   out_3939009506131001575[3] = 0;
   out_3939009506131001575[4] = 0;
   out_3939009506131001575[5] = 0;
   out_3939009506131001575[6] = 1;
   out_3939009506131001575[7] = 0;
   out_3939009506131001575[8] = 0;
   out_3939009506131001575[9] = 1;
   out_3939009506131001575[10] = 0;
   out_3939009506131001575[11] = 0;
   out_3939009506131001575[12] = 0;
   out_3939009506131001575[13] = 0;
   out_3939009506131001575[14] = 0;
   out_3939009506131001575[15] = 0;
   out_3939009506131001575[16] = 0;
   out_3939009506131001575[17] = 0;
   out_3939009506131001575[18] = 0;
   out_3939009506131001575[19] = 0;
   out_3939009506131001575[20] = 0;
   out_3939009506131001575[21] = 0;
   out_3939009506131001575[22] = 0;
   out_3939009506131001575[23] = 0;
   out_3939009506131001575[24] = 0;
   out_3939009506131001575[25] = 1;
   out_3939009506131001575[26] = 0;
   out_3939009506131001575[27] = 0;
   out_3939009506131001575[28] = 1;
   out_3939009506131001575[29] = 0;
   out_3939009506131001575[30] = 0;
   out_3939009506131001575[31] = 0;
   out_3939009506131001575[32] = 0;
   out_3939009506131001575[33] = 0;
   out_3939009506131001575[34] = 0;
   out_3939009506131001575[35] = 0;
   out_3939009506131001575[36] = 0;
   out_3939009506131001575[37] = 0;
   out_3939009506131001575[38] = 0;
   out_3939009506131001575[39] = 0;
   out_3939009506131001575[40] = 0;
   out_3939009506131001575[41] = 0;
   out_3939009506131001575[42] = 0;
   out_3939009506131001575[43] = 0;
   out_3939009506131001575[44] = 1;
   out_3939009506131001575[45] = 0;
   out_3939009506131001575[46] = 0;
   out_3939009506131001575[47] = 1;
   out_3939009506131001575[48] = 0;
   out_3939009506131001575[49] = 0;
   out_3939009506131001575[50] = 0;
   out_3939009506131001575[51] = 0;
   out_3939009506131001575[52] = 0;
   out_3939009506131001575[53] = 0;
}
void h_10(double *state, double *unused, double *out_1655604040140950053) {
   out_1655604040140950053[0] = 9.8100000000000005*sin(state[1]) - state[4]*state[8] + state[5]*state[7] + state[12] + state[15];
   out_1655604040140950053[1] = -9.8100000000000005*sin(state[0])*cos(state[1]) + state[3]*state[8] - state[5]*state[6] + state[13] + state[16];
   out_1655604040140950053[2] = -9.8100000000000005*cos(state[0])*cos(state[1]) - state[3]*state[7] + state[4]*state[6] + state[14] + state[17];
}
void H_10(double *state, double *unused, double *out_4967479801708401183) {
   out_4967479801708401183[0] = 0;
   out_4967479801708401183[1] = 9.8100000000000005*cos(state[1]);
   out_4967479801708401183[2] = 0;
   out_4967479801708401183[3] = 0;
   out_4967479801708401183[4] = -state[8];
   out_4967479801708401183[5] = state[7];
   out_4967479801708401183[6] = 0;
   out_4967479801708401183[7] = state[5];
   out_4967479801708401183[8] = -state[4];
   out_4967479801708401183[9] = 0;
   out_4967479801708401183[10] = 0;
   out_4967479801708401183[11] = 0;
   out_4967479801708401183[12] = 1;
   out_4967479801708401183[13] = 0;
   out_4967479801708401183[14] = 0;
   out_4967479801708401183[15] = 1;
   out_4967479801708401183[16] = 0;
   out_4967479801708401183[17] = 0;
   out_4967479801708401183[18] = -9.8100000000000005*cos(state[0])*cos(state[1]);
   out_4967479801708401183[19] = 9.8100000000000005*sin(state[0])*sin(state[1]);
   out_4967479801708401183[20] = 0;
   out_4967479801708401183[21] = state[8];
   out_4967479801708401183[22] = 0;
   out_4967479801708401183[23] = -state[6];
   out_4967479801708401183[24] = -state[5];
   out_4967479801708401183[25] = 0;
   out_4967479801708401183[26] = state[3];
   out_4967479801708401183[27] = 0;
   out_4967479801708401183[28] = 0;
   out_4967479801708401183[29] = 0;
   out_4967479801708401183[30] = 0;
   out_4967479801708401183[31] = 1;
   out_4967479801708401183[32] = 0;
   out_4967479801708401183[33] = 0;
   out_4967479801708401183[34] = 1;
   out_4967479801708401183[35] = 0;
   out_4967479801708401183[36] = 9.8100000000000005*sin(state[0])*cos(state[1]);
   out_4967479801708401183[37] = 9.8100000000000005*sin(state[1])*cos(state[0]);
   out_4967479801708401183[38] = 0;
   out_4967479801708401183[39] = -state[7];
   out_4967479801708401183[40] = state[6];
   out_4967479801708401183[41] = 0;
   out_4967479801708401183[42] = state[4];
   out_4967479801708401183[43] = -state[3];
   out_4967479801708401183[44] = 0;
   out_4967479801708401183[45] = 0;
   out_4967479801708401183[46] = 0;
   out_4967479801708401183[47] = 0;
   out_4967479801708401183[48] = 0;
   out_4967479801708401183[49] = 0;
   out_4967479801708401183[50] = 1;
   out_4967479801708401183[51] = 0;
   out_4967479801708401183[52] = 0;
   out_4967479801708401183[53] = 1;
}
void h_13(double *state, double *unused, double *out_8625473817892073850) {
   out_8625473817892073850[0] = state[3];
   out_8625473817892073850[1] = state[4];
   out_8625473817892073850[2] = state[5];
}
void H_13(double *state, double *unused, double *out_726735680798668774) {
   out_726735680798668774[0] = 0;
   out_726735680798668774[1] = 0;
   out_726735680798668774[2] = 0;
   out_726735680798668774[3] = 1;
   out_726735680798668774[4] = 0;
   out_726735680798668774[5] = 0;
   out_726735680798668774[6] = 0;
   out_726735680798668774[7] = 0;
   out_726735680798668774[8] = 0;
   out_726735680798668774[9] = 0;
   out_726735680798668774[10] = 0;
   out_726735680798668774[11] = 0;
   out_726735680798668774[12] = 0;
   out_726735680798668774[13] = 0;
   out_726735680798668774[14] = 0;
   out_726735680798668774[15] = 0;
   out_726735680798668774[16] = 0;
   out_726735680798668774[17] = 0;
   out_726735680798668774[18] = 0;
   out_726735680798668774[19] = 0;
   out_726735680798668774[20] = 0;
   out_726735680798668774[21] = 0;
   out_726735680798668774[22] = 1;
   out_726735680798668774[23] = 0;
   out_726735680798668774[24] = 0;
   out_726735680798668774[25] = 0;
   out_726735680798668774[26] = 0;
   out_726735680798668774[27] = 0;
   out_726735680798668774[28] = 0;
   out_726735680798668774[29] = 0;
   out_726735680798668774[30] = 0;
   out_726735680798668774[31] = 0;
   out_726735680798668774[32] = 0;
   out_726735680798668774[33] = 0;
   out_726735680798668774[34] = 0;
   out_726735680798668774[35] = 0;
   out_726735680798668774[36] = 0;
   out_726735680798668774[37] = 0;
   out_726735680798668774[38] = 0;
   out_726735680798668774[39] = 0;
   out_726735680798668774[40] = 0;
   out_726735680798668774[41] = 1;
   out_726735680798668774[42] = 0;
   out_726735680798668774[43] = 0;
   out_726735680798668774[44] = 0;
   out_726735680798668774[45] = 0;
   out_726735680798668774[46] = 0;
   out_726735680798668774[47] = 0;
   out_726735680798668774[48] = 0;
   out_726735680798668774[49] = 0;
   out_726735680798668774[50] = 0;
   out_726735680798668774[51] = 0;
   out_726735680798668774[52] = 0;
   out_726735680798668774[53] = 0;
}
void h_14(double *state, double *unused, double *out_8584103974170844119) {
   out_8584103974170844119[0] = state[6];
   out_8584103974170844119[1] = state[7];
   out_8584103974170844119[2] = state[8];
}
void H_14(double *state, double *unused, double *out_7021797938426373871) {
   out_7021797938426373871[0] = 0;
   out_7021797938426373871[1] = 0;
   out_7021797938426373871[2] = 0;
   out_7021797938426373871[3] = 0;
   out_7021797938426373871[4] = 0;
   out_7021797938426373871[5] = 0;
   out_7021797938426373871[6] = 1;
   out_7021797938426373871[7] = 0;
   out_7021797938426373871[8] = 0;
   out_7021797938426373871[9] = 0;
   out_7021797938426373871[10] = 0;
   out_7021797938426373871[11] = 0;
   out_7021797938426373871[12] = 0;
   out_7021797938426373871[13] = 0;
   out_7021797938426373871[14] = 0;
   out_7021797938426373871[15] = 0;
   out_7021797938426373871[16] = 0;
   out_7021797938426373871[17] = 0;
   out_7021797938426373871[18] = 0;
   out_7021797938426373871[19] = 0;
   out_7021797938426373871[20] = 0;
   out_7021797938426373871[21] = 0;
   out_7021797938426373871[22] = 0;
   out_7021797938426373871[23] = 0;
   out_7021797938426373871[24] = 0;
   out_7021797938426373871[25] = 1;
   out_7021797938426373871[26] = 0;
   out_7021797938426373871[27] = 0;
   out_7021797938426373871[28] = 0;
   out_7021797938426373871[29] = 0;
   out_7021797938426373871[30] = 0;
   out_7021797938426373871[31] = 0;
   out_7021797938426373871[32] = 0;
   out_7021797938426373871[33] = 0;
   out_7021797938426373871[34] = 0;
   out_7021797938426373871[35] = 0;
   out_7021797938426373871[36] = 0;
   out_7021797938426373871[37] = 0;
   out_7021797938426373871[38] = 0;
   out_7021797938426373871[39] = 0;
   out_7021797938426373871[40] = 0;
   out_7021797938426373871[41] = 0;
   out_7021797938426373871[42] = 0;
   out_7021797938426373871[43] = 0;
   out_7021797938426373871[44] = 1;
   out_7021797938426373871[45] = 0;
   out_7021797938426373871[46] = 0;
   out_7021797938426373871[47] = 0;
   out_7021797938426373871[48] = 0;
   out_7021797938426373871[49] = 0;
   out_7021797938426373871[50] = 0;
   out_7021797938426373871[51] = 0;
   out_7021797938426373871[52] = 0;
   out_7021797938426373871[53] = 0;
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
void pose_err_fun(double *nom_x, double *delta_x, double *out_3394550637581824468) {
  err_fun(nom_x, delta_x, out_3394550637581824468);
}
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_774672115471856853) {
  inv_err_fun(nom_x, true_x, out_774672115471856853);
}
void pose_H_mod_fun(double *state, double *out_7710816715974909147) {
  H_mod_fun(state, out_7710816715974909147);
}
void pose_f_fun(double *state, double dt, double *out_5487839870694824154) {
  f_fun(state,  dt, out_5487839870694824154);
}
void pose_F_fun(double *state, double dt, double *out_5336850415855987983) {
  F_fun(state,  dt, out_5336850415855987983);
}
void pose_h_4(double *state, double *unused, double *out_7487667227305404692) {
  h_4(state, unused, out_7487667227305404692);
}
void pose_H_4(double *state, double *unused, double *out_3939009506131001575) {
  H_4(state, unused, out_3939009506131001575);
}
void pose_h_10(double *state, double *unused, double *out_1655604040140950053) {
  h_10(state, unused, out_1655604040140950053);
}
void pose_H_10(double *state, double *unused, double *out_4967479801708401183) {
  H_10(state, unused, out_4967479801708401183);
}
void pose_h_13(double *state, double *unused, double *out_8625473817892073850) {
  h_13(state, unused, out_8625473817892073850);
}
void pose_H_13(double *state, double *unused, double *out_726735680798668774) {
  H_13(state, unused, out_726735680798668774);
}
void pose_h_14(double *state, double *unused, double *out_8584103974170844119) {
  h_14(state, unused, out_8584103974170844119);
}
void pose_H_14(double *state, double *unused, double *out_7021797938426373871) {
  H_14(state, unused, out_7021797938426373871);
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
