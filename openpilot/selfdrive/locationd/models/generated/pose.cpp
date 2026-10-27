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
void err_fun(double *nom_x, double *delta_x, double *out_8760976694843722585) {
   out_8760976694843722585[0] = delta_x[0] + nom_x[0];
   out_8760976694843722585[1] = delta_x[1] + nom_x[1];
   out_8760976694843722585[2] = delta_x[2] + nom_x[2];
   out_8760976694843722585[3] = delta_x[3] + nom_x[3];
   out_8760976694843722585[4] = delta_x[4] + nom_x[4];
   out_8760976694843722585[5] = delta_x[5] + nom_x[5];
   out_8760976694843722585[6] = delta_x[6] + nom_x[6];
   out_8760976694843722585[7] = delta_x[7] + nom_x[7];
   out_8760976694843722585[8] = delta_x[8] + nom_x[8];
   out_8760976694843722585[9] = delta_x[9] + nom_x[9];
   out_8760976694843722585[10] = delta_x[10] + nom_x[10];
   out_8760976694843722585[11] = delta_x[11] + nom_x[11];
   out_8760976694843722585[12] = delta_x[12] + nom_x[12];
   out_8760976694843722585[13] = delta_x[13] + nom_x[13];
   out_8760976694843722585[14] = delta_x[14] + nom_x[14];
   out_8760976694843722585[15] = delta_x[15] + nom_x[15];
   out_8760976694843722585[16] = delta_x[16] + nom_x[16];
   out_8760976694843722585[17] = delta_x[17] + nom_x[17];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_43912959781476086) {
   out_43912959781476086[0] = -nom_x[0] + true_x[0];
   out_43912959781476086[1] = -nom_x[1] + true_x[1];
   out_43912959781476086[2] = -nom_x[2] + true_x[2];
   out_43912959781476086[3] = -nom_x[3] + true_x[3];
   out_43912959781476086[4] = -nom_x[4] + true_x[4];
   out_43912959781476086[5] = -nom_x[5] + true_x[5];
   out_43912959781476086[6] = -nom_x[6] + true_x[6];
   out_43912959781476086[7] = -nom_x[7] + true_x[7];
   out_43912959781476086[8] = -nom_x[8] + true_x[8];
   out_43912959781476086[9] = -nom_x[9] + true_x[9];
   out_43912959781476086[10] = -nom_x[10] + true_x[10];
   out_43912959781476086[11] = -nom_x[11] + true_x[11];
   out_43912959781476086[12] = -nom_x[12] + true_x[12];
   out_43912959781476086[13] = -nom_x[13] + true_x[13];
   out_43912959781476086[14] = -nom_x[14] + true_x[14];
   out_43912959781476086[15] = -nom_x[15] + true_x[15];
   out_43912959781476086[16] = -nom_x[16] + true_x[16];
   out_43912959781476086[17] = -nom_x[17] + true_x[17];
}
void H_mod_fun(double *state, double *out_7299666891344506350) {
   out_7299666891344506350[0] = 1.0;
   out_7299666891344506350[1] = 0.0;
   out_7299666891344506350[2] = 0.0;
   out_7299666891344506350[3] = 0.0;
   out_7299666891344506350[4] = 0.0;
   out_7299666891344506350[5] = 0.0;
   out_7299666891344506350[6] = 0.0;
   out_7299666891344506350[7] = 0.0;
   out_7299666891344506350[8] = 0.0;
   out_7299666891344506350[9] = 0.0;
   out_7299666891344506350[10] = 0.0;
   out_7299666891344506350[11] = 0.0;
   out_7299666891344506350[12] = 0.0;
   out_7299666891344506350[13] = 0.0;
   out_7299666891344506350[14] = 0.0;
   out_7299666891344506350[15] = 0.0;
   out_7299666891344506350[16] = 0.0;
   out_7299666891344506350[17] = 0.0;
   out_7299666891344506350[18] = 0.0;
   out_7299666891344506350[19] = 1.0;
   out_7299666891344506350[20] = 0.0;
   out_7299666891344506350[21] = 0.0;
   out_7299666891344506350[22] = 0.0;
   out_7299666891344506350[23] = 0.0;
   out_7299666891344506350[24] = 0.0;
   out_7299666891344506350[25] = 0.0;
   out_7299666891344506350[26] = 0.0;
   out_7299666891344506350[27] = 0.0;
   out_7299666891344506350[28] = 0.0;
   out_7299666891344506350[29] = 0.0;
   out_7299666891344506350[30] = 0.0;
   out_7299666891344506350[31] = 0.0;
   out_7299666891344506350[32] = 0.0;
   out_7299666891344506350[33] = 0.0;
   out_7299666891344506350[34] = 0.0;
   out_7299666891344506350[35] = 0.0;
   out_7299666891344506350[36] = 0.0;
   out_7299666891344506350[37] = 0.0;
   out_7299666891344506350[38] = 1.0;
   out_7299666891344506350[39] = 0.0;
   out_7299666891344506350[40] = 0.0;
   out_7299666891344506350[41] = 0.0;
   out_7299666891344506350[42] = 0.0;
   out_7299666891344506350[43] = 0.0;
   out_7299666891344506350[44] = 0.0;
   out_7299666891344506350[45] = 0.0;
   out_7299666891344506350[46] = 0.0;
   out_7299666891344506350[47] = 0.0;
   out_7299666891344506350[48] = 0.0;
   out_7299666891344506350[49] = 0.0;
   out_7299666891344506350[50] = 0.0;
   out_7299666891344506350[51] = 0.0;
   out_7299666891344506350[52] = 0.0;
   out_7299666891344506350[53] = 0.0;
   out_7299666891344506350[54] = 0.0;
   out_7299666891344506350[55] = 0.0;
   out_7299666891344506350[56] = 0.0;
   out_7299666891344506350[57] = 1.0;
   out_7299666891344506350[58] = 0.0;
   out_7299666891344506350[59] = 0.0;
   out_7299666891344506350[60] = 0.0;
   out_7299666891344506350[61] = 0.0;
   out_7299666891344506350[62] = 0.0;
   out_7299666891344506350[63] = 0.0;
   out_7299666891344506350[64] = 0.0;
   out_7299666891344506350[65] = 0.0;
   out_7299666891344506350[66] = 0.0;
   out_7299666891344506350[67] = 0.0;
   out_7299666891344506350[68] = 0.0;
   out_7299666891344506350[69] = 0.0;
   out_7299666891344506350[70] = 0.0;
   out_7299666891344506350[71] = 0.0;
   out_7299666891344506350[72] = 0.0;
   out_7299666891344506350[73] = 0.0;
   out_7299666891344506350[74] = 0.0;
   out_7299666891344506350[75] = 0.0;
   out_7299666891344506350[76] = 1.0;
   out_7299666891344506350[77] = 0.0;
   out_7299666891344506350[78] = 0.0;
   out_7299666891344506350[79] = 0.0;
   out_7299666891344506350[80] = 0.0;
   out_7299666891344506350[81] = 0.0;
   out_7299666891344506350[82] = 0.0;
   out_7299666891344506350[83] = 0.0;
   out_7299666891344506350[84] = 0.0;
   out_7299666891344506350[85] = 0.0;
   out_7299666891344506350[86] = 0.0;
   out_7299666891344506350[87] = 0.0;
   out_7299666891344506350[88] = 0.0;
   out_7299666891344506350[89] = 0.0;
   out_7299666891344506350[90] = 0.0;
   out_7299666891344506350[91] = 0.0;
   out_7299666891344506350[92] = 0.0;
   out_7299666891344506350[93] = 0.0;
   out_7299666891344506350[94] = 0.0;
   out_7299666891344506350[95] = 1.0;
   out_7299666891344506350[96] = 0.0;
   out_7299666891344506350[97] = 0.0;
   out_7299666891344506350[98] = 0.0;
   out_7299666891344506350[99] = 0.0;
   out_7299666891344506350[100] = 0.0;
   out_7299666891344506350[101] = 0.0;
   out_7299666891344506350[102] = 0.0;
   out_7299666891344506350[103] = 0.0;
   out_7299666891344506350[104] = 0.0;
   out_7299666891344506350[105] = 0.0;
   out_7299666891344506350[106] = 0.0;
   out_7299666891344506350[107] = 0.0;
   out_7299666891344506350[108] = 0.0;
   out_7299666891344506350[109] = 0.0;
   out_7299666891344506350[110] = 0.0;
   out_7299666891344506350[111] = 0.0;
   out_7299666891344506350[112] = 0.0;
   out_7299666891344506350[113] = 0.0;
   out_7299666891344506350[114] = 1.0;
   out_7299666891344506350[115] = 0.0;
   out_7299666891344506350[116] = 0.0;
   out_7299666891344506350[117] = 0.0;
   out_7299666891344506350[118] = 0.0;
   out_7299666891344506350[119] = 0.0;
   out_7299666891344506350[120] = 0.0;
   out_7299666891344506350[121] = 0.0;
   out_7299666891344506350[122] = 0.0;
   out_7299666891344506350[123] = 0.0;
   out_7299666891344506350[124] = 0.0;
   out_7299666891344506350[125] = 0.0;
   out_7299666891344506350[126] = 0.0;
   out_7299666891344506350[127] = 0.0;
   out_7299666891344506350[128] = 0.0;
   out_7299666891344506350[129] = 0.0;
   out_7299666891344506350[130] = 0.0;
   out_7299666891344506350[131] = 0.0;
   out_7299666891344506350[132] = 0.0;
   out_7299666891344506350[133] = 1.0;
   out_7299666891344506350[134] = 0.0;
   out_7299666891344506350[135] = 0.0;
   out_7299666891344506350[136] = 0.0;
   out_7299666891344506350[137] = 0.0;
   out_7299666891344506350[138] = 0.0;
   out_7299666891344506350[139] = 0.0;
   out_7299666891344506350[140] = 0.0;
   out_7299666891344506350[141] = 0.0;
   out_7299666891344506350[142] = 0.0;
   out_7299666891344506350[143] = 0.0;
   out_7299666891344506350[144] = 0.0;
   out_7299666891344506350[145] = 0.0;
   out_7299666891344506350[146] = 0.0;
   out_7299666891344506350[147] = 0.0;
   out_7299666891344506350[148] = 0.0;
   out_7299666891344506350[149] = 0.0;
   out_7299666891344506350[150] = 0.0;
   out_7299666891344506350[151] = 0.0;
   out_7299666891344506350[152] = 1.0;
   out_7299666891344506350[153] = 0.0;
   out_7299666891344506350[154] = 0.0;
   out_7299666891344506350[155] = 0.0;
   out_7299666891344506350[156] = 0.0;
   out_7299666891344506350[157] = 0.0;
   out_7299666891344506350[158] = 0.0;
   out_7299666891344506350[159] = 0.0;
   out_7299666891344506350[160] = 0.0;
   out_7299666891344506350[161] = 0.0;
   out_7299666891344506350[162] = 0.0;
   out_7299666891344506350[163] = 0.0;
   out_7299666891344506350[164] = 0.0;
   out_7299666891344506350[165] = 0.0;
   out_7299666891344506350[166] = 0.0;
   out_7299666891344506350[167] = 0.0;
   out_7299666891344506350[168] = 0.0;
   out_7299666891344506350[169] = 0.0;
   out_7299666891344506350[170] = 0.0;
   out_7299666891344506350[171] = 1.0;
   out_7299666891344506350[172] = 0.0;
   out_7299666891344506350[173] = 0.0;
   out_7299666891344506350[174] = 0.0;
   out_7299666891344506350[175] = 0.0;
   out_7299666891344506350[176] = 0.0;
   out_7299666891344506350[177] = 0.0;
   out_7299666891344506350[178] = 0.0;
   out_7299666891344506350[179] = 0.0;
   out_7299666891344506350[180] = 0.0;
   out_7299666891344506350[181] = 0.0;
   out_7299666891344506350[182] = 0.0;
   out_7299666891344506350[183] = 0.0;
   out_7299666891344506350[184] = 0.0;
   out_7299666891344506350[185] = 0.0;
   out_7299666891344506350[186] = 0.0;
   out_7299666891344506350[187] = 0.0;
   out_7299666891344506350[188] = 0.0;
   out_7299666891344506350[189] = 0.0;
   out_7299666891344506350[190] = 1.0;
   out_7299666891344506350[191] = 0.0;
   out_7299666891344506350[192] = 0.0;
   out_7299666891344506350[193] = 0.0;
   out_7299666891344506350[194] = 0.0;
   out_7299666891344506350[195] = 0.0;
   out_7299666891344506350[196] = 0.0;
   out_7299666891344506350[197] = 0.0;
   out_7299666891344506350[198] = 0.0;
   out_7299666891344506350[199] = 0.0;
   out_7299666891344506350[200] = 0.0;
   out_7299666891344506350[201] = 0.0;
   out_7299666891344506350[202] = 0.0;
   out_7299666891344506350[203] = 0.0;
   out_7299666891344506350[204] = 0.0;
   out_7299666891344506350[205] = 0.0;
   out_7299666891344506350[206] = 0.0;
   out_7299666891344506350[207] = 0.0;
   out_7299666891344506350[208] = 0.0;
   out_7299666891344506350[209] = 1.0;
   out_7299666891344506350[210] = 0.0;
   out_7299666891344506350[211] = 0.0;
   out_7299666891344506350[212] = 0.0;
   out_7299666891344506350[213] = 0.0;
   out_7299666891344506350[214] = 0.0;
   out_7299666891344506350[215] = 0.0;
   out_7299666891344506350[216] = 0.0;
   out_7299666891344506350[217] = 0.0;
   out_7299666891344506350[218] = 0.0;
   out_7299666891344506350[219] = 0.0;
   out_7299666891344506350[220] = 0.0;
   out_7299666891344506350[221] = 0.0;
   out_7299666891344506350[222] = 0.0;
   out_7299666891344506350[223] = 0.0;
   out_7299666891344506350[224] = 0.0;
   out_7299666891344506350[225] = 0.0;
   out_7299666891344506350[226] = 0.0;
   out_7299666891344506350[227] = 0.0;
   out_7299666891344506350[228] = 1.0;
   out_7299666891344506350[229] = 0.0;
   out_7299666891344506350[230] = 0.0;
   out_7299666891344506350[231] = 0.0;
   out_7299666891344506350[232] = 0.0;
   out_7299666891344506350[233] = 0.0;
   out_7299666891344506350[234] = 0.0;
   out_7299666891344506350[235] = 0.0;
   out_7299666891344506350[236] = 0.0;
   out_7299666891344506350[237] = 0.0;
   out_7299666891344506350[238] = 0.0;
   out_7299666891344506350[239] = 0.0;
   out_7299666891344506350[240] = 0.0;
   out_7299666891344506350[241] = 0.0;
   out_7299666891344506350[242] = 0.0;
   out_7299666891344506350[243] = 0.0;
   out_7299666891344506350[244] = 0.0;
   out_7299666891344506350[245] = 0.0;
   out_7299666891344506350[246] = 0.0;
   out_7299666891344506350[247] = 1.0;
   out_7299666891344506350[248] = 0.0;
   out_7299666891344506350[249] = 0.0;
   out_7299666891344506350[250] = 0.0;
   out_7299666891344506350[251] = 0.0;
   out_7299666891344506350[252] = 0.0;
   out_7299666891344506350[253] = 0.0;
   out_7299666891344506350[254] = 0.0;
   out_7299666891344506350[255] = 0.0;
   out_7299666891344506350[256] = 0.0;
   out_7299666891344506350[257] = 0.0;
   out_7299666891344506350[258] = 0.0;
   out_7299666891344506350[259] = 0.0;
   out_7299666891344506350[260] = 0.0;
   out_7299666891344506350[261] = 0.0;
   out_7299666891344506350[262] = 0.0;
   out_7299666891344506350[263] = 0.0;
   out_7299666891344506350[264] = 0.0;
   out_7299666891344506350[265] = 0.0;
   out_7299666891344506350[266] = 1.0;
   out_7299666891344506350[267] = 0.0;
   out_7299666891344506350[268] = 0.0;
   out_7299666891344506350[269] = 0.0;
   out_7299666891344506350[270] = 0.0;
   out_7299666891344506350[271] = 0.0;
   out_7299666891344506350[272] = 0.0;
   out_7299666891344506350[273] = 0.0;
   out_7299666891344506350[274] = 0.0;
   out_7299666891344506350[275] = 0.0;
   out_7299666891344506350[276] = 0.0;
   out_7299666891344506350[277] = 0.0;
   out_7299666891344506350[278] = 0.0;
   out_7299666891344506350[279] = 0.0;
   out_7299666891344506350[280] = 0.0;
   out_7299666891344506350[281] = 0.0;
   out_7299666891344506350[282] = 0.0;
   out_7299666891344506350[283] = 0.0;
   out_7299666891344506350[284] = 0.0;
   out_7299666891344506350[285] = 1.0;
   out_7299666891344506350[286] = 0.0;
   out_7299666891344506350[287] = 0.0;
   out_7299666891344506350[288] = 0.0;
   out_7299666891344506350[289] = 0.0;
   out_7299666891344506350[290] = 0.0;
   out_7299666891344506350[291] = 0.0;
   out_7299666891344506350[292] = 0.0;
   out_7299666891344506350[293] = 0.0;
   out_7299666891344506350[294] = 0.0;
   out_7299666891344506350[295] = 0.0;
   out_7299666891344506350[296] = 0.0;
   out_7299666891344506350[297] = 0.0;
   out_7299666891344506350[298] = 0.0;
   out_7299666891344506350[299] = 0.0;
   out_7299666891344506350[300] = 0.0;
   out_7299666891344506350[301] = 0.0;
   out_7299666891344506350[302] = 0.0;
   out_7299666891344506350[303] = 0.0;
   out_7299666891344506350[304] = 1.0;
   out_7299666891344506350[305] = 0.0;
   out_7299666891344506350[306] = 0.0;
   out_7299666891344506350[307] = 0.0;
   out_7299666891344506350[308] = 0.0;
   out_7299666891344506350[309] = 0.0;
   out_7299666891344506350[310] = 0.0;
   out_7299666891344506350[311] = 0.0;
   out_7299666891344506350[312] = 0.0;
   out_7299666891344506350[313] = 0.0;
   out_7299666891344506350[314] = 0.0;
   out_7299666891344506350[315] = 0.0;
   out_7299666891344506350[316] = 0.0;
   out_7299666891344506350[317] = 0.0;
   out_7299666891344506350[318] = 0.0;
   out_7299666891344506350[319] = 0.0;
   out_7299666891344506350[320] = 0.0;
   out_7299666891344506350[321] = 0.0;
   out_7299666891344506350[322] = 0.0;
   out_7299666891344506350[323] = 1.0;
}
void f_fun(double *state, double dt, double *out_8034507002781912440) {
   out_8034507002781912440[0] = atan2((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), -(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]));
   out_8034507002781912440[1] = asin(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]));
   out_8034507002781912440[2] = atan2(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), -(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]));
   out_8034507002781912440[3] = dt*state[12] + state[3];
   out_8034507002781912440[4] = dt*state[13] + state[4];
   out_8034507002781912440[5] = dt*state[14] + state[5];
   out_8034507002781912440[6] = state[6];
   out_8034507002781912440[7] = state[7];
   out_8034507002781912440[8] = state[8];
   out_8034507002781912440[9] = state[9];
   out_8034507002781912440[10] = state[10];
   out_8034507002781912440[11] = state[11];
   out_8034507002781912440[12] = state[12];
   out_8034507002781912440[13] = state[13];
   out_8034507002781912440[14] = state[14];
   out_8034507002781912440[15] = state[15];
   out_8034507002781912440[16] = state[16];
   out_8034507002781912440[17] = state[17];
}
void F_fun(double *state, double dt, double *out_1438095572352487590) {
   out_1438095572352487590[0] = ((-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*cos(state[0])*cos(state[1]) - sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*cos(state[0])*cos(state[1]) - sin(dt*state[6])*sin(state[0])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_1438095572352487590[1] = ((-sin(dt*state[6])*sin(dt*state[8]) - sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*cos(state[1]) - (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*sin(state[1]) - sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(state[0]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*sin(state[1]) + (-sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) + sin(dt*state[8])*cos(dt*state[6]))*cos(state[1]) - sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(state[0]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_1438095572352487590[2] = 0;
   out_1438095572352487590[3] = 0;
   out_1438095572352487590[4] = 0;
   out_1438095572352487590[5] = 0;
   out_1438095572352487590[6] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(dt*cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) - dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_1438095572352487590[7] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*sin(dt*state[7])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[6])*sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) - dt*sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[7])*cos(dt*state[6])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[8])*sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]) - dt*sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_1438095572352487590[8] = ((dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((dt*sin(dt*state[6])*sin(dt*state[8]) + dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_1438095572352487590[9] = 0;
   out_1438095572352487590[10] = 0;
   out_1438095572352487590[11] = 0;
   out_1438095572352487590[12] = 0;
   out_1438095572352487590[13] = 0;
   out_1438095572352487590[14] = 0;
   out_1438095572352487590[15] = 0;
   out_1438095572352487590[16] = 0;
   out_1438095572352487590[17] = 0;
   out_1438095572352487590[18] = (-sin(dt*state[7])*sin(state[0])*cos(state[1]) - sin(dt*state[8])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_1438095572352487590[19] = (-sin(dt*state[7])*sin(state[1])*cos(state[0]) + sin(dt*state[8])*sin(state[0])*sin(state[1])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_1438095572352487590[20] = 0;
   out_1438095572352487590[21] = 0;
   out_1438095572352487590[22] = 0;
   out_1438095572352487590[23] = 0;
   out_1438095572352487590[24] = 0;
   out_1438095572352487590[25] = (dt*sin(dt*state[7])*sin(dt*state[8])*sin(state[0])*cos(state[1]) - dt*sin(dt*state[7])*sin(state[1])*cos(dt*state[8]) + dt*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_1438095572352487590[26] = (-dt*sin(dt*state[8])*sin(state[1])*cos(dt*state[7]) - dt*sin(state[0])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_1438095572352487590[27] = 0;
   out_1438095572352487590[28] = 0;
   out_1438095572352487590[29] = 0;
   out_1438095572352487590[30] = 0;
   out_1438095572352487590[31] = 0;
   out_1438095572352487590[32] = 0;
   out_1438095572352487590[33] = 0;
   out_1438095572352487590[34] = 0;
   out_1438095572352487590[35] = 0;
   out_1438095572352487590[36] = ((sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_1438095572352487590[37] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-sin(dt*state[7])*sin(state[2])*cos(state[0])*cos(state[1]) + sin(dt*state[8])*sin(state[0])*sin(state[2])*cos(dt*state[7])*cos(state[1]) - sin(state[1])*sin(state[2])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(-sin(dt*state[7])*cos(state[0])*cos(state[1])*cos(state[2]) + sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1])*cos(state[2]) - sin(state[1])*cos(dt*state[7])*cos(dt*state[8])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_1438095572352487590[38] = ((-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (-sin(state[0])*sin(state[1])*sin(state[2]) - cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_1438095572352487590[39] = 0;
   out_1438095572352487590[40] = 0;
   out_1438095572352487590[41] = 0;
   out_1438095572352487590[42] = 0;
   out_1438095572352487590[43] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(dt*(sin(state[0])*cos(state[2]) - sin(state[1])*sin(state[2])*cos(state[0]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*sin(state[2])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(dt*(-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_1438095572352487590[44] = (dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*sin(state[2])*cos(dt*state[7])*cos(state[1]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + (dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[7])*cos(state[1])*cos(state[2]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_1438095572352487590[45] = 0;
   out_1438095572352487590[46] = 0;
   out_1438095572352487590[47] = 0;
   out_1438095572352487590[48] = 0;
   out_1438095572352487590[49] = 0;
   out_1438095572352487590[50] = 0;
   out_1438095572352487590[51] = 0;
   out_1438095572352487590[52] = 0;
   out_1438095572352487590[53] = 0;
   out_1438095572352487590[54] = 0;
   out_1438095572352487590[55] = 0;
   out_1438095572352487590[56] = 0;
   out_1438095572352487590[57] = 1;
   out_1438095572352487590[58] = 0;
   out_1438095572352487590[59] = 0;
   out_1438095572352487590[60] = 0;
   out_1438095572352487590[61] = 0;
   out_1438095572352487590[62] = 0;
   out_1438095572352487590[63] = 0;
   out_1438095572352487590[64] = 0;
   out_1438095572352487590[65] = 0;
   out_1438095572352487590[66] = dt;
   out_1438095572352487590[67] = 0;
   out_1438095572352487590[68] = 0;
   out_1438095572352487590[69] = 0;
   out_1438095572352487590[70] = 0;
   out_1438095572352487590[71] = 0;
   out_1438095572352487590[72] = 0;
   out_1438095572352487590[73] = 0;
   out_1438095572352487590[74] = 0;
   out_1438095572352487590[75] = 0;
   out_1438095572352487590[76] = 1;
   out_1438095572352487590[77] = 0;
   out_1438095572352487590[78] = 0;
   out_1438095572352487590[79] = 0;
   out_1438095572352487590[80] = 0;
   out_1438095572352487590[81] = 0;
   out_1438095572352487590[82] = 0;
   out_1438095572352487590[83] = 0;
   out_1438095572352487590[84] = 0;
   out_1438095572352487590[85] = dt;
   out_1438095572352487590[86] = 0;
   out_1438095572352487590[87] = 0;
   out_1438095572352487590[88] = 0;
   out_1438095572352487590[89] = 0;
   out_1438095572352487590[90] = 0;
   out_1438095572352487590[91] = 0;
   out_1438095572352487590[92] = 0;
   out_1438095572352487590[93] = 0;
   out_1438095572352487590[94] = 0;
   out_1438095572352487590[95] = 1;
   out_1438095572352487590[96] = 0;
   out_1438095572352487590[97] = 0;
   out_1438095572352487590[98] = 0;
   out_1438095572352487590[99] = 0;
   out_1438095572352487590[100] = 0;
   out_1438095572352487590[101] = 0;
   out_1438095572352487590[102] = 0;
   out_1438095572352487590[103] = 0;
   out_1438095572352487590[104] = dt;
   out_1438095572352487590[105] = 0;
   out_1438095572352487590[106] = 0;
   out_1438095572352487590[107] = 0;
   out_1438095572352487590[108] = 0;
   out_1438095572352487590[109] = 0;
   out_1438095572352487590[110] = 0;
   out_1438095572352487590[111] = 0;
   out_1438095572352487590[112] = 0;
   out_1438095572352487590[113] = 0;
   out_1438095572352487590[114] = 1;
   out_1438095572352487590[115] = 0;
   out_1438095572352487590[116] = 0;
   out_1438095572352487590[117] = 0;
   out_1438095572352487590[118] = 0;
   out_1438095572352487590[119] = 0;
   out_1438095572352487590[120] = 0;
   out_1438095572352487590[121] = 0;
   out_1438095572352487590[122] = 0;
   out_1438095572352487590[123] = 0;
   out_1438095572352487590[124] = 0;
   out_1438095572352487590[125] = 0;
   out_1438095572352487590[126] = 0;
   out_1438095572352487590[127] = 0;
   out_1438095572352487590[128] = 0;
   out_1438095572352487590[129] = 0;
   out_1438095572352487590[130] = 0;
   out_1438095572352487590[131] = 0;
   out_1438095572352487590[132] = 0;
   out_1438095572352487590[133] = 1;
   out_1438095572352487590[134] = 0;
   out_1438095572352487590[135] = 0;
   out_1438095572352487590[136] = 0;
   out_1438095572352487590[137] = 0;
   out_1438095572352487590[138] = 0;
   out_1438095572352487590[139] = 0;
   out_1438095572352487590[140] = 0;
   out_1438095572352487590[141] = 0;
   out_1438095572352487590[142] = 0;
   out_1438095572352487590[143] = 0;
   out_1438095572352487590[144] = 0;
   out_1438095572352487590[145] = 0;
   out_1438095572352487590[146] = 0;
   out_1438095572352487590[147] = 0;
   out_1438095572352487590[148] = 0;
   out_1438095572352487590[149] = 0;
   out_1438095572352487590[150] = 0;
   out_1438095572352487590[151] = 0;
   out_1438095572352487590[152] = 1;
   out_1438095572352487590[153] = 0;
   out_1438095572352487590[154] = 0;
   out_1438095572352487590[155] = 0;
   out_1438095572352487590[156] = 0;
   out_1438095572352487590[157] = 0;
   out_1438095572352487590[158] = 0;
   out_1438095572352487590[159] = 0;
   out_1438095572352487590[160] = 0;
   out_1438095572352487590[161] = 0;
   out_1438095572352487590[162] = 0;
   out_1438095572352487590[163] = 0;
   out_1438095572352487590[164] = 0;
   out_1438095572352487590[165] = 0;
   out_1438095572352487590[166] = 0;
   out_1438095572352487590[167] = 0;
   out_1438095572352487590[168] = 0;
   out_1438095572352487590[169] = 0;
   out_1438095572352487590[170] = 0;
   out_1438095572352487590[171] = 1;
   out_1438095572352487590[172] = 0;
   out_1438095572352487590[173] = 0;
   out_1438095572352487590[174] = 0;
   out_1438095572352487590[175] = 0;
   out_1438095572352487590[176] = 0;
   out_1438095572352487590[177] = 0;
   out_1438095572352487590[178] = 0;
   out_1438095572352487590[179] = 0;
   out_1438095572352487590[180] = 0;
   out_1438095572352487590[181] = 0;
   out_1438095572352487590[182] = 0;
   out_1438095572352487590[183] = 0;
   out_1438095572352487590[184] = 0;
   out_1438095572352487590[185] = 0;
   out_1438095572352487590[186] = 0;
   out_1438095572352487590[187] = 0;
   out_1438095572352487590[188] = 0;
   out_1438095572352487590[189] = 0;
   out_1438095572352487590[190] = 1;
   out_1438095572352487590[191] = 0;
   out_1438095572352487590[192] = 0;
   out_1438095572352487590[193] = 0;
   out_1438095572352487590[194] = 0;
   out_1438095572352487590[195] = 0;
   out_1438095572352487590[196] = 0;
   out_1438095572352487590[197] = 0;
   out_1438095572352487590[198] = 0;
   out_1438095572352487590[199] = 0;
   out_1438095572352487590[200] = 0;
   out_1438095572352487590[201] = 0;
   out_1438095572352487590[202] = 0;
   out_1438095572352487590[203] = 0;
   out_1438095572352487590[204] = 0;
   out_1438095572352487590[205] = 0;
   out_1438095572352487590[206] = 0;
   out_1438095572352487590[207] = 0;
   out_1438095572352487590[208] = 0;
   out_1438095572352487590[209] = 1;
   out_1438095572352487590[210] = 0;
   out_1438095572352487590[211] = 0;
   out_1438095572352487590[212] = 0;
   out_1438095572352487590[213] = 0;
   out_1438095572352487590[214] = 0;
   out_1438095572352487590[215] = 0;
   out_1438095572352487590[216] = 0;
   out_1438095572352487590[217] = 0;
   out_1438095572352487590[218] = 0;
   out_1438095572352487590[219] = 0;
   out_1438095572352487590[220] = 0;
   out_1438095572352487590[221] = 0;
   out_1438095572352487590[222] = 0;
   out_1438095572352487590[223] = 0;
   out_1438095572352487590[224] = 0;
   out_1438095572352487590[225] = 0;
   out_1438095572352487590[226] = 0;
   out_1438095572352487590[227] = 0;
   out_1438095572352487590[228] = 1;
   out_1438095572352487590[229] = 0;
   out_1438095572352487590[230] = 0;
   out_1438095572352487590[231] = 0;
   out_1438095572352487590[232] = 0;
   out_1438095572352487590[233] = 0;
   out_1438095572352487590[234] = 0;
   out_1438095572352487590[235] = 0;
   out_1438095572352487590[236] = 0;
   out_1438095572352487590[237] = 0;
   out_1438095572352487590[238] = 0;
   out_1438095572352487590[239] = 0;
   out_1438095572352487590[240] = 0;
   out_1438095572352487590[241] = 0;
   out_1438095572352487590[242] = 0;
   out_1438095572352487590[243] = 0;
   out_1438095572352487590[244] = 0;
   out_1438095572352487590[245] = 0;
   out_1438095572352487590[246] = 0;
   out_1438095572352487590[247] = 1;
   out_1438095572352487590[248] = 0;
   out_1438095572352487590[249] = 0;
   out_1438095572352487590[250] = 0;
   out_1438095572352487590[251] = 0;
   out_1438095572352487590[252] = 0;
   out_1438095572352487590[253] = 0;
   out_1438095572352487590[254] = 0;
   out_1438095572352487590[255] = 0;
   out_1438095572352487590[256] = 0;
   out_1438095572352487590[257] = 0;
   out_1438095572352487590[258] = 0;
   out_1438095572352487590[259] = 0;
   out_1438095572352487590[260] = 0;
   out_1438095572352487590[261] = 0;
   out_1438095572352487590[262] = 0;
   out_1438095572352487590[263] = 0;
   out_1438095572352487590[264] = 0;
   out_1438095572352487590[265] = 0;
   out_1438095572352487590[266] = 1;
   out_1438095572352487590[267] = 0;
   out_1438095572352487590[268] = 0;
   out_1438095572352487590[269] = 0;
   out_1438095572352487590[270] = 0;
   out_1438095572352487590[271] = 0;
   out_1438095572352487590[272] = 0;
   out_1438095572352487590[273] = 0;
   out_1438095572352487590[274] = 0;
   out_1438095572352487590[275] = 0;
   out_1438095572352487590[276] = 0;
   out_1438095572352487590[277] = 0;
   out_1438095572352487590[278] = 0;
   out_1438095572352487590[279] = 0;
   out_1438095572352487590[280] = 0;
   out_1438095572352487590[281] = 0;
   out_1438095572352487590[282] = 0;
   out_1438095572352487590[283] = 0;
   out_1438095572352487590[284] = 0;
   out_1438095572352487590[285] = 1;
   out_1438095572352487590[286] = 0;
   out_1438095572352487590[287] = 0;
   out_1438095572352487590[288] = 0;
   out_1438095572352487590[289] = 0;
   out_1438095572352487590[290] = 0;
   out_1438095572352487590[291] = 0;
   out_1438095572352487590[292] = 0;
   out_1438095572352487590[293] = 0;
   out_1438095572352487590[294] = 0;
   out_1438095572352487590[295] = 0;
   out_1438095572352487590[296] = 0;
   out_1438095572352487590[297] = 0;
   out_1438095572352487590[298] = 0;
   out_1438095572352487590[299] = 0;
   out_1438095572352487590[300] = 0;
   out_1438095572352487590[301] = 0;
   out_1438095572352487590[302] = 0;
   out_1438095572352487590[303] = 0;
   out_1438095572352487590[304] = 1;
   out_1438095572352487590[305] = 0;
   out_1438095572352487590[306] = 0;
   out_1438095572352487590[307] = 0;
   out_1438095572352487590[308] = 0;
   out_1438095572352487590[309] = 0;
   out_1438095572352487590[310] = 0;
   out_1438095572352487590[311] = 0;
   out_1438095572352487590[312] = 0;
   out_1438095572352487590[313] = 0;
   out_1438095572352487590[314] = 0;
   out_1438095572352487590[315] = 0;
   out_1438095572352487590[316] = 0;
   out_1438095572352487590[317] = 0;
   out_1438095572352487590[318] = 0;
   out_1438095572352487590[319] = 0;
   out_1438095572352487590[320] = 0;
   out_1438095572352487590[321] = 0;
   out_1438095572352487590[322] = 0;
   out_1438095572352487590[323] = 1;
}
void h_4(double *state, double *unused, double *out_6465945623265405794) {
   out_6465945623265405794[0] = state[6] + state[9];
   out_6465945623265405794[1] = state[7] + state[10];
   out_6465945623265405794[2] = state[8] + state[11];
}
void H_4(double *state, double *unused, double *out_1438529340738482788) {
   out_1438529340738482788[0] = 0;
   out_1438529340738482788[1] = 0;
   out_1438529340738482788[2] = 0;
   out_1438529340738482788[3] = 0;
   out_1438529340738482788[4] = 0;
   out_1438529340738482788[5] = 0;
   out_1438529340738482788[6] = 1;
   out_1438529340738482788[7] = 0;
   out_1438529340738482788[8] = 0;
   out_1438529340738482788[9] = 1;
   out_1438529340738482788[10] = 0;
   out_1438529340738482788[11] = 0;
   out_1438529340738482788[12] = 0;
   out_1438529340738482788[13] = 0;
   out_1438529340738482788[14] = 0;
   out_1438529340738482788[15] = 0;
   out_1438529340738482788[16] = 0;
   out_1438529340738482788[17] = 0;
   out_1438529340738482788[18] = 0;
   out_1438529340738482788[19] = 0;
   out_1438529340738482788[20] = 0;
   out_1438529340738482788[21] = 0;
   out_1438529340738482788[22] = 0;
   out_1438529340738482788[23] = 0;
   out_1438529340738482788[24] = 0;
   out_1438529340738482788[25] = 1;
   out_1438529340738482788[26] = 0;
   out_1438529340738482788[27] = 0;
   out_1438529340738482788[28] = 1;
   out_1438529340738482788[29] = 0;
   out_1438529340738482788[30] = 0;
   out_1438529340738482788[31] = 0;
   out_1438529340738482788[32] = 0;
   out_1438529340738482788[33] = 0;
   out_1438529340738482788[34] = 0;
   out_1438529340738482788[35] = 0;
   out_1438529340738482788[36] = 0;
   out_1438529340738482788[37] = 0;
   out_1438529340738482788[38] = 0;
   out_1438529340738482788[39] = 0;
   out_1438529340738482788[40] = 0;
   out_1438529340738482788[41] = 0;
   out_1438529340738482788[42] = 0;
   out_1438529340738482788[43] = 0;
   out_1438529340738482788[44] = 1;
   out_1438529340738482788[45] = 0;
   out_1438529340738482788[46] = 0;
   out_1438529340738482788[47] = 1;
   out_1438529340738482788[48] = 0;
   out_1438529340738482788[49] = 0;
   out_1438529340738482788[50] = 0;
   out_1438529340738482788[51] = 0;
   out_1438529340738482788[52] = 0;
   out_1438529340738482788[53] = 0;
}
void h_10(double *state, double *unused, double *out_648283545540513810) {
   out_648283545540513810[0] = 9.8100000000000005*sin(state[1]) - state[4]*state[8] + state[5]*state[7] + state[12] + state[15];
   out_648283545540513810[1] = -9.8100000000000005*sin(state[0])*cos(state[1]) + state[3]*state[8] - state[5]*state[6] + state[13] + state[16];
   out_648283545540513810[2] = -9.8100000000000005*cos(state[0])*cos(state[1]) - state[3]*state[7] + state[4]*state[6] + state[14] + state[17];
}
void H_10(double *state, double *unused, double *out_3602654715956183362) {
   out_3602654715956183362[0] = 0;
   out_3602654715956183362[1] = 9.8100000000000005*cos(state[1]);
   out_3602654715956183362[2] = 0;
   out_3602654715956183362[3] = 0;
   out_3602654715956183362[4] = -state[8];
   out_3602654715956183362[5] = state[7];
   out_3602654715956183362[6] = 0;
   out_3602654715956183362[7] = state[5];
   out_3602654715956183362[8] = -state[4];
   out_3602654715956183362[9] = 0;
   out_3602654715956183362[10] = 0;
   out_3602654715956183362[11] = 0;
   out_3602654715956183362[12] = 1;
   out_3602654715956183362[13] = 0;
   out_3602654715956183362[14] = 0;
   out_3602654715956183362[15] = 1;
   out_3602654715956183362[16] = 0;
   out_3602654715956183362[17] = 0;
   out_3602654715956183362[18] = -9.8100000000000005*cos(state[0])*cos(state[1]);
   out_3602654715956183362[19] = 9.8100000000000005*sin(state[0])*sin(state[1]);
   out_3602654715956183362[20] = 0;
   out_3602654715956183362[21] = state[8];
   out_3602654715956183362[22] = 0;
   out_3602654715956183362[23] = -state[6];
   out_3602654715956183362[24] = -state[5];
   out_3602654715956183362[25] = 0;
   out_3602654715956183362[26] = state[3];
   out_3602654715956183362[27] = 0;
   out_3602654715956183362[28] = 0;
   out_3602654715956183362[29] = 0;
   out_3602654715956183362[30] = 0;
   out_3602654715956183362[31] = 1;
   out_3602654715956183362[32] = 0;
   out_3602654715956183362[33] = 0;
   out_3602654715956183362[34] = 1;
   out_3602654715956183362[35] = 0;
   out_3602654715956183362[36] = 9.8100000000000005*sin(state[0])*cos(state[1]);
   out_3602654715956183362[37] = 9.8100000000000005*sin(state[1])*cos(state[0]);
   out_3602654715956183362[38] = 0;
   out_3602654715956183362[39] = -state[7];
   out_3602654715956183362[40] = state[6];
   out_3602654715956183362[41] = 0;
   out_3602654715956183362[42] = state[4];
   out_3602654715956183362[43] = -state[3];
   out_3602654715956183362[44] = 0;
   out_3602654715956183362[45] = 0;
   out_3602654715956183362[46] = 0;
   out_3602654715956183362[47] = 0;
   out_3602654715956183362[48] = 0;
   out_3602654715956183362[49] = 0;
   out_3602654715956183362[50] = 1;
   out_3602654715956183362[51] = 0;
   out_3602654715956183362[52] = 0;
   out_3602654715956183362[53] = 1;
}
void h_13(double *state, double *unused, double *out_4712435644913014) {
   out_4712435644913014[0] = state[3];
   out_4712435644913014[1] = state[4];
   out_4712435644913014[2] = state[5];
}
void H_13(double *state, double *unused, double *out_4650803166070815589) {
   out_4650803166070815589[0] = 0;
   out_4650803166070815589[1] = 0;
   out_4650803166070815589[2] = 0;
   out_4650803166070815589[3] = 1;
   out_4650803166070815589[4] = 0;
   out_4650803166070815589[5] = 0;
   out_4650803166070815589[6] = 0;
   out_4650803166070815589[7] = 0;
   out_4650803166070815589[8] = 0;
   out_4650803166070815589[9] = 0;
   out_4650803166070815589[10] = 0;
   out_4650803166070815589[11] = 0;
   out_4650803166070815589[12] = 0;
   out_4650803166070815589[13] = 0;
   out_4650803166070815589[14] = 0;
   out_4650803166070815589[15] = 0;
   out_4650803166070815589[16] = 0;
   out_4650803166070815589[17] = 0;
   out_4650803166070815589[18] = 0;
   out_4650803166070815589[19] = 0;
   out_4650803166070815589[20] = 0;
   out_4650803166070815589[21] = 0;
   out_4650803166070815589[22] = 1;
   out_4650803166070815589[23] = 0;
   out_4650803166070815589[24] = 0;
   out_4650803166070815589[25] = 0;
   out_4650803166070815589[26] = 0;
   out_4650803166070815589[27] = 0;
   out_4650803166070815589[28] = 0;
   out_4650803166070815589[29] = 0;
   out_4650803166070815589[30] = 0;
   out_4650803166070815589[31] = 0;
   out_4650803166070815589[32] = 0;
   out_4650803166070815589[33] = 0;
   out_4650803166070815589[34] = 0;
   out_4650803166070815589[35] = 0;
   out_4650803166070815589[36] = 0;
   out_4650803166070815589[37] = 0;
   out_4650803166070815589[38] = 0;
   out_4650803166070815589[39] = 0;
   out_4650803166070815589[40] = 0;
   out_4650803166070815589[41] = 1;
   out_4650803166070815589[42] = 0;
   out_4650803166070815589[43] = 0;
   out_4650803166070815589[44] = 0;
   out_4650803166070815589[45] = 0;
   out_4650803166070815589[46] = 0;
   out_4650803166070815589[47] = 0;
   out_4650803166070815589[48] = 0;
   out_4650803166070815589[49] = 0;
   out_4650803166070815589[50] = 0;
   out_4650803166070815589[51] = 0;
   out_4650803166070815589[52] = 0;
   out_4650803166070815589[53] = 0;
}
void h_14(double *state, double *unused, double *out_3818899265695519350) {
   out_3818899265695519350[0] = state[6];
   out_3818899265695519350[1] = state[7];
   out_3818899265695519350[2] = state[8];
}
void H_14(double *state, double *unused, double *out_5401770197077967317) {
   out_5401770197077967317[0] = 0;
   out_5401770197077967317[1] = 0;
   out_5401770197077967317[2] = 0;
   out_5401770197077967317[3] = 0;
   out_5401770197077967317[4] = 0;
   out_5401770197077967317[5] = 0;
   out_5401770197077967317[6] = 1;
   out_5401770197077967317[7] = 0;
   out_5401770197077967317[8] = 0;
   out_5401770197077967317[9] = 0;
   out_5401770197077967317[10] = 0;
   out_5401770197077967317[11] = 0;
   out_5401770197077967317[12] = 0;
   out_5401770197077967317[13] = 0;
   out_5401770197077967317[14] = 0;
   out_5401770197077967317[15] = 0;
   out_5401770197077967317[16] = 0;
   out_5401770197077967317[17] = 0;
   out_5401770197077967317[18] = 0;
   out_5401770197077967317[19] = 0;
   out_5401770197077967317[20] = 0;
   out_5401770197077967317[21] = 0;
   out_5401770197077967317[22] = 0;
   out_5401770197077967317[23] = 0;
   out_5401770197077967317[24] = 0;
   out_5401770197077967317[25] = 1;
   out_5401770197077967317[26] = 0;
   out_5401770197077967317[27] = 0;
   out_5401770197077967317[28] = 0;
   out_5401770197077967317[29] = 0;
   out_5401770197077967317[30] = 0;
   out_5401770197077967317[31] = 0;
   out_5401770197077967317[32] = 0;
   out_5401770197077967317[33] = 0;
   out_5401770197077967317[34] = 0;
   out_5401770197077967317[35] = 0;
   out_5401770197077967317[36] = 0;
   out_5401770197077967317[37] = 0;
   out_5401770197077967317[38] = 0;
   out_5401770197077967317[39] = 0;
   out_5401770197077967317[40] = 0;
   out_5401770197077967317[41] = 0;
   out_5401770197077967317[42] = 0;
   out_5401770197077967317[43] = 0;
   out_5401770197077967317[44] = 1;
   out_5401770197077967317[45] = 0;
   out_5401770197077967317[46] = 0;
   out_5401770197077967317[47] = 0;
   out_5401770197077967317[48] = 0;
   out_5401770197077967317[49] = 0;
   out_5401770197077967317[50] = 0;
   out_5401770197077967317[51] = 0;
   out_5401770197077967317[52] = 0;
   out_5401770197077967317[53] = 0;
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
void pose_err_fun(double *nom_x, double *delta_x, double *out_8760976694843722585) {
  err_fun(nom_x, delta_x, out_8760976694843722585);
}
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_43912959781476086) {
  inv_err_fun(nom_x, true_x, out_43912959781476086);
}
void pose_H_mod_fun(double *state, double *out_7299666891344506350) {
  H_mod_fun(state, out_7299666891344506350);
}
void pose_f_fun(double *state, double dt, double *out_8034507002781912440) {
  f_fun(state,  dt, out_8034507002781912440);
}
void pose_F_fun(double *state, double dt, double *out_1438095572352487590) {
  F_fun(state,  dt, out_1438095572352487590);
}
void pose_h_4(double *state, double *unused, double *out_6465945623265405794) {
  h_4(state, unused, out_6465945623265405794);
}
void pose_H_4(double *state, double *unused, double *out_1438529340738482788) {
  H_4(state, unused, out_1438529340738482788);
}
void pose_h_10(double *state, double *unused, double *out_648283545540513810) {
  h_10(state, unused, out_648283545540513810);
}
void pose_H_10(double *state, double *unused, double *out_3602654715956183362) {
  H_10(state, unused, out_3602654715956183362);
}
void pose_h_13(double *state, double *unused, double *out_4712435644913014) {
  h_13(state, unused, out_4712435644913014);
}
void pose_H_13(double *state, double *unused, double *out_4650803166070815589) {
  H_13(state, unused, out_4650803166070815589);
}
void pose_h_14(double *state, double *unused, double *out_3818899265695519350) {
  h_14(state, unused, out_3818899265695519350);
}
void pose_H_14(double *state, double *unused, double *out_5401770197077967317) {
  H_14(state, unused, out_5401770197077967317);
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
