#include "car.h"

namespace {
#define DIM 9
#define EDIM 9
#define MEDIM 9
typedef void (*Hfun)(double *, double *, double *);

double mass;

void set_mass(double x){ mass = x;}

double rotational_inertia;

void set_rotational_inertia(double x){ rotational_inertia = x;}

double center_to_front;

void set_center_to_front(double x){ center_to_front = x;}

double center_to_rear;

void set_center_to_rear(double x){ center_to_rear = x;}

double stiffness_front;

void set_stiffness_front(double x){ stiffness_front = x;}

double stiffness_rear;

void set_stiffness_rear(double x){ stiffness_rear = x;}
const static double MAHA_THRESH_25 = 3.8414588206941227;
const static double MAHA_THRESH_24 = 5.991464547107981;
const static double MAHA_THRESH_30 = 3.8414588206941227;
const static double MAHA_THRESH_26 = 3.8414588206941227;
const static double MAHA_THRESH_27 = 3.8414588206941227;
const static double MAHA_THRESH_29 = 3.8414588206941227;
const static double MAHA_THRESH_28 = 3.8414588206941227;
const static double MAHA_THRESH_31 = 3.8414588206941227;

/******************************************************************************
 *                      Code generated with SymPy 1.13.2                      *
 *                                                                            *
 *              See http://www.sympy.org/ for more information.               *
 *                                                                            *
 *                         This file is part of 'ekf'                         *
 ******************************************************************************/
void err_fun(double *nom_x, double *delta_x, double *out_9074734778873374225) {
   out_9074734778873374225[0] = delta_x[0] + nom_x[0];
   out_9074734778873374225[1] = delta_x[1] + nom_x[1];
   out_9074734778873374225[2] = delta_x[2] + nom_x[2];
   out_9074734778873374225[3] = delta_x[3] + nom_x[3];
   out_9074734778873374225[4] = delta_x[4] + nom_x[4];
   out_9074734778873374225[5] = delta_x[5] + nom_x[5];
   out_9074734778873374225[6] = delta_x[6] + nom_x[6];
   out_9074734778873374225[7] = delta_x[7] + nom_x[7];
   out_9074734778873374225[8] = delta_x[8] + nom_x[8];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_8103998558374365190) {
   out_8103998558374365190[0] = -nom_x[0] + true_x[0];
   out_8103998558374365190[1] = -nom_x[1] + true_x[1];
   out_8103998558374365190[2] = -nom_x[2] + true_x[2];
   out_8103998558374365190[3] = -nom_x[3] + true_x[3];
   out_8103998558374365190[4] = -nom_x[4] + true_x[4];
   out_8103998558374365190[5] = -nom_x[5] + true_x[5];
   out_8103998558374365190[6] = -nom_x[6] + true_x[6];
   out_8103998558374365190[7] = -nom_x[7] + true_x[7];
   out_8103998558374365190[8] = -nom_x[8] + true_x[8];
}
void H_mod_fun(double *state, double *out_387978277478947035) {
   out_387978277478947035[0] = 1.0;
   out_387978277478947035[1] = 0.0;
   out_387978277478947035[2] = 0.0;
   out_387978277478947035[3] = 0.0;
   out_387978277478947035[4] = 0.0;
   out_387978277478947035[5] = 0.0;
   out_387978277478947035[6] = 0.0;
   out_387978277478947035[7] = 0.0;
   out_387978277478947035[8] = 0.0;
   out_387978277478947035[9] = 0.0;
   out_387978277478947035[10] = 1.0;
   out_387978277478947035[11] = 0.0;
   out_387978277478947035[12] = 0.0;
   out_387978277478947035[13] = 0.0;
   out_387978277478947035[14] = 0.0;
   out_387978277478947035[15] = 0.0;
   out_387978277478947035[16] = 0.0;
   out_387978277478947035[17] = 0.0;
   out_387978277478947035[18] = 0.0;
   out_387978277478947035[19] = 0.0;
   out_387978277478947035[20] = 1.0;
   out_387978277478947035[21] = 0.0;
   out_387978277478947035[22] = 0.0;
   out_387978277478947035[23] = 0.0;
   out_387978277478947035[24] = 0.0;
   out_387978277478947035[25] = 0.0;
   out_387978277478947035[26] = 0.0;
   out_387978277478947035[27] = 0.0;
   out_387978277478947035[28] = 0.0;
   out_387978277478947035[29] = 0.0;
   out_387978277478947035[30] = 1.0;
   out_387978277478947035[31] = 0.0;
   out_387978277478947035[32] = 0.0;
   out_387978277478947035[33] = 0.0;
   out_387978277478947035[34] = 0.0;
   out_387978277478947035[35] = 0.0;
   out_387978277478947035[36] = 0.0;
   out_387978277478947035[37] = 0.0;
   out_387978277478947035[38] = 0.0;
   out_387978277478947035[39] = 0.0;
   out_387978277478947035[40] = 1.0;
   out_387978277478947035[41] = 0.0;
   out_387978277478947035[42] = 0.0;
   out_387978277478947035[43] = 0.0;
   out_387978277478947035[44] = 0.0;
   out_387978277478947035[45] = 0.0;
   out_387978277478947035[46] = 0.0;
   out_387978277478947035[47] = 0.0;
   out_387978277478947035[48] = 0.0;
   out_387978277478947035[49] = 0.0;
   out_387978277478947035[50] = 1.0;
   out_387978277478947035[51] = 0.0;
   out_387978277478947035[52] = 0.0;
   out_387978277478947035[53] = 0.0;
   out_387978277478947035[54] = 0.0;
   out_387978277478947035[55] = 0.0;
   out_387978277478947035[56] = 0.0;
   out_387978277478947035[57] = 0.0;
   out_387978277478947035[58] = 0.0;
   out_387978277478947035[59] = 0.0;
   out_387978277478947035[60] = 1.0;
   out_387978277478947035[61] = 0.0;
   out_387978277478947035[62] = 0.0;
   out_387978277478947035[63] = 0.0;
   out_387978277478947035[64] = 0.0;
   out_387978277478947035[65] = 0.0;
   out_387978277478947035[66] = 0.0;
   out_387978277478947035[67] = 0.0;
   out_387978277478947035[68] = 0.0;
   out_387978277478947035[69] = 0.0;
   out_387978277478947035[70] = 1.0;
   out_387978277478947035[71] = 0.0;
   out_387978277478947035[72] = 0.0;
   out_387978277478947035[73] = 0.0;
   out_387978277478947035[74] = 0.0;
   out_387978277478947035[75] = 0.0;
   out_387978277478947035[76] = 0.0;
   out_387978277478947035[77] = 0.0;
   out_387978277478947035[78] = 0.0;
   out_387978277478947035[79] = 0.0;
   out_387978277478947035[80] = 1.0;
}
void f_fun(double *state, double dt, double *out_4763203206369738804) {
   out_4763203206369738804[0] = state[0];
   out_4763203206369738804[1] = state[1];
   out_4763203206369738804[2] = state[2];
   out_4763203206369738804[3] = state[3];
   out_4763203206369738804[4] = state[4];
   out_4763203206369738804[5] = dt*((-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]))*state[6] - 9.8000000000000007*state[8] + stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*state[1]) + (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*state[4])) + state[5];
   out_4763203206369738804[6] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*state[4])) + state[6];
   out_4763203206369738804[7] = state[7];
   out_4763203206369738804[8] = state[8];
}
void F_fun(double *state, double dt, double *out_1016500512322045568) {
   out_1016500512322045568[0] = 1;
   out_1016500512322045568[1] = 0;
   out_1016500512322045568[2] = 0;
   out_1016500512322045568[3] = 0;
   out_1016500512322045568[4] = 0;
   out_1016500512322045568[5] = 0;
   out_1016500512322045568[6] = 0;
   out_1016500512322045568[7] = 0;
   out_1016500512322045568[8] = 0;
   out_1016500512322045568[9] = 0;
   out_1016500512322045568[10] = 1;
   out_1016500512322045568[11] = 0;
   out_1016500512322045568[12] = 0;
   out_1016500512322045568[13] = 0;
   out_1016500512322045568[14] = 0;
   out_1016500512322045568[15] = 0;
   out_1016500512322045568[16] = 0;
   out_1016500512322045568[17] = 0;
   out_1016500512322045568[18] = 0;
   out_1016500512322045568[19] = 0;
   out_1016500512322045568[20] = 1;
   out_1016500512322045568[21] = 0;
   out_1016500512322045568[22] = 0;
   out_1016500512322045568[23] = 0;
   out_1016500512322045568[24] = 0;
   out_1016500512322045568[25] = 0;
   out_1016500512322045568[26] = 0;
   out_1016500512322045568[27] = 0;
   out_1016500512322045568[28] = 0;
   out_1016500512322045568[29] = 0;
   out_1016500512322045568[30] = 1;
   out_1016500512322045568[31] = 0;
   out_1016500512322045568[32] = 0;
   out_1016500512322045568[33] = 0;
   out_1016500512322045568[34] = 0;
   out_1016500512322045568[35] = 0;
   out_1016500512322045568[36] = 0;
   out_1016500512322045568[37] = 0;
   out_1016500512322045568[38] = 0;
   out_1016500512322045568[39] = 0;
   out_1016500512322045568[40] = 1;
   out_1016500512322045568[41] = 0;
   out_1016500512322045568[42] = 0;
   out_1016500512322045568[43] = 0;
   out_1016500512322045568[44] = 0;
   out_1016500512322045568[45] = dt*(stiffness_front*(-state[2] - state[3] + state[7])/(mass*state[1]) + (-stiffness_front - stiffness_rear)*state[5]/(mass*state[4]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[6]/(mass*state[4]));
   out_1016500512322045568[46] = -dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*pow(state[1], 2));
   out_1016500512322045568[47] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_1016500512322045568[48] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_1016500512322045568[49] = dt*((-1 - (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*pow(state[4], 2)))*state[6] - (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*pow(state[4], 2)));
   out_1016500512322045568[50] = dt*(-stiffness_front*state[0] - stiffness_rear*state[0])/(mass*state[4]) + 1;
   out_1016500512322045568[51] = dt*(-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]));
   out_1016500512322045568[52] = dt*stiffness_front*state[0]/(mass*state[1]);
   out_1016500512322045568[53] = -9.8000000000000007*dt;
   out_1016500512322045568[54] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front - pow(center_to_rear, 2)*stiffness_rear)*state[6]/(rotational_inertia*state[4]));
   out_1016500512322045568[55] = -center_to_front*dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*pow(state[1], 2));
   out_1016500512322045568[56] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_1016500512322045568[57] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_1016500512322045568[58] = dt*(-(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*pow(state[4], 2)) - (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*pow(state[4], 2)));
   out_1016500512322045568[59] = dt*(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(rotational_inertia*state[4]);
   out_1016500512322045568[60] = dt*(-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])/(rotational_inertia*state[4]) + 1;
   out_1016500512322045568[61] = center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_1016500512322045568[62] = 0;
   out_1016500512322045568[63] = 0;
   out_1016500512322045568[64] = 0;
   out_1016500512322045568[65] = 0;
   out_1016500512322045568[66] = 0;
   out_1016500512322045568[67] = 0;
   out_1016500512322045568[68] = 0;
   out_1016500512322045568[69] = 0;
   out_1016500512322045568[70] = 1;
   out_1016500512322045568[71] = 0;
   out_1016500512322045568[72] = 0;
   out_1016500512322045568[73] = 0;
   out_1016500512322045568[74] = 0;
   out_1016500512322045568[75] = 0;
   out_1016500512322045568[76] = 0;
   out_1016500512322045568[77] = 0;
   out_1016500512322045568[78] = 0;
   out_1016500512322045568[79] = 0;
   out_1016500512322045568[80] = 1;
}
void h_25(double *state, double *unused, double *out_1860729718252120477) {
   out_1860729718252120477[0] = state[6];
}
void H_25(double *state, double *unused, double *out_9152136137538215632) {
   out_9152136137538215632[0] = 0;
   out_9152136137538215632[1] = 0;
   out_9152136137538215632[2] = 0;
   out_9152136137538215632[3] = 0;
   out_9152136137538215632[4] = 0;
   out_9152136137538215632[5] = 0;
   out_9152136137538215632[6] = 1;
   out_9152136137538215632[7] = 0;
   out_9152136137538215632[8] = 0;
}
void h_24(double *state, double *unused, double *out_694198277336709874) {
   out_694198277336709874[0] = state[4];
   out_694198277336709874[1] = state[5];
}
void H_24(double *state, double *unused, double *out_5736682337369012848) {
   out_5736682337369012848[0] = 0;
   out_5736682337369012848[1] = 0;
   out_5736682337369012848[2] = 0;
   out_5736682337369012848[3] = 0;
   out_5736682337369012848[4] = 1;
   out_5736682337369012848[5] = 0;
   out_5736682337369012848[6] = 0;
   out_5736682337369012848[7] = 0;
   out_5736682337369012848[8] = 0;
   out_5736682337369012848[9] = 0;
   out_5736682337369012848[10] = 0;
   out_5736682337369012848[11] = 0;
   out_5736682337369012848[12] = 0;
   out_5736682337369012848[13] = 0;
   out_5736682337369012848[14] = 1;
   out_5736682337369012848[15] = 0;
   out_5736682337369012848[16] = 0;
   out_5736682337369012848[17] = 0;
}
void h_30(double *state, double *unused, double *out_2984511561861269912) {
   out_2984511561861269912[0] = state[4];
}
void H_30(double *state, double *unused, double *out_6776274977664087357) {
   out_6776274977664087357[0] = 0;
   out_6776274977664087357[1] = 0;
   out_6776274977664087357[2] = 0;
   out_6776274977664087357[3] = 0;
   out_6776274977664087357[4] = 1;
   out_6776274977664087357[5] = 0;
   out_6776274977664087357[6] = 0;
   out_6776274977664087357[7] = 0;
   out_6776274977664087357[8] = 0;
}
void h_26(double *state, double *unused, double *out_6665923047582284564) {
   out_6665923047582284564[0] = state[7];
}
void H_26(double *state, double *unused, double *out_5990081966410535383) {
   out_5990081966410535383[0] = 0;
   out_5990081966410535383[1] = 0;
   out_5990081966410535383[2] = 0;
   out_5990081966410535383[3] = 0;
   out_5990081966410535383[4] = 0;
   out_5990081966410535383[5] = 0;
   out_5990081966410535383[6] = 0;
   out_5990081966410535383[7] = 1;
   out_5990081966410535383[8] = 0;
}
void h_27(double *state, double *unused, double *out_1555543571396949539) {
   out_1555543571396949539[0] = state[3];
}
void H_27(double *state, double *unused, double *out_8951038289464512268) {
   out_8951038289464512268[0] = 0;
   out_8951038289464512268[1] = 0;
   out_8951038289464512268[2] = 0;
   out_8951038289464512268[3] = 1;
   out_8951038289464512268[4] = 0;
   out_8951038289464512268[5] = 0;
   out_8951038289464512268[6] = 0;
   out_8951038289464512268[7] = 0;
   out_8951038289464512268[8] = 0;
}
void h_29(double *state, double *unused, double *out_8326378797747300475) {
   out_8326378797747300475[0] = state[1];
}
void H_29(double *state, double *unused, double *out_6266043633349695173) {
   out_6266043633349695173[0] = 0;
   out_6266043633349695173[1] = 1;
   out_6266043633349695173[2] = 0;
   out_6266043633349695173[3] = 0;
   out_6266043633349695173[4] = 0;
   out_6266043633349695173[5] = 0;
   out_6266043633349695173[6] = 0;
   out_6266043633349695173[7] = 0;
   out_6266043633349695173[8] = 0;
}
void h_28(double *state, double *unused, double *out_3446129696263896106) {
   out_3446129696263896106[0] = state[0];
}
void H_28(double *state, double *unused, double *out_7098301423290325869) {
   out_7098301423290325869[0] = 1;
   out_7098301423290325869[1] = 0;
   out_7098301423290325869[2] = 0;
   out_7098301423290325869[3] = 0;
   out_7098301423290325869[4] = 0;
   out_7098301423290325869[5] = 0;
   out_7098301423290325869[6] = 0;
   out_7098301423290325869[7] = 0;
   out_7098301423290325869[8] = 0;
}
void h_31(double *state, double *unused, double *out_6020542932501928708) {
   out_6020542932501928708[0] = state[8];
}
void H_31(double *state, double *unused, double *out_6616290068643886859) {
   out_6616290068643886859[0] = 0;
   out_6616290068643886859[1] = 0;
   out_6616290068643886859[2] = 0;
   out_6616290068643886859[3] = 0;
   out_6616290068643886859[4] = 0;
   out_6616290068643886859[5] = 0;
   out_6616290068643886859[6] = 0;
   out_6616290068643886859[7] = 0;
   out_6616290068643886859[8] = 1;
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

void car_update_25(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_25, H_25, NULL, in_z, in_R, in_ea, MAHA_THRESH_25);
}
void car_update_24(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<2, 3, 0>(in_x, in_P, h_24, H_24, NULL, in_z, in_R, in_ea, MAHA_THRESH_24);
}
void car_update_30(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_30, H_30, NULL, in_z, in_R, in_ea, MAHA_THRESH_30);
}
void car_update_26(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_26, H_26, NULL, in_z, in_R, in_ea, MAHA_THRESH_26);
}
void car_update_27(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_27, H_27, NULL, in_z, in_R, in_ea, MAHA_THRESH_27);
}
void car_update_29(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_29, H_29, NULL, in_z, in_R, in_ea, MAHA_THRESH_29);
}
void car_update_28(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_28, H_28, NULL, in_z, in_R, in_ea, MAHA_THRESH_28);
}
void car_update_31(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_31, H_31, NULL, in_z, in_R, in_ea, MAHA_THRESH_31);
}
void car_err_fun(double *nom_x, double *delta_x, double *out_9074734778873374225) {
  err_fun(nom_x, delta_x, out_9074734778873374225);
}
void car_inv_err_fun(double *nom_x, double *true_x, double *out_8103998558374365190) {
  inv_err_fun(nom_x, true_x, out_8103998558374365190);
}
void car_H_mod_fun(double *state, double *out_387978277478947035) {
  H_mod_fun(state, out_387978277478947035);
}
void car_f_fun(double *state, double dt, double *out_4763203206369738804) {
  f_fun(state,  dt, out_4763203206369738804);
}
void car_F_fun(double *state, double dt, double *out_1016500512322045568) {
  F_fun(state,  dt, out_1016500512322045568);
}
void car_h_25(double *state, double *unused, double *out_1860729718252120477) {
  h_25(state, unused, out_1860729718252120477);
}
void car_H_25(double *state, double *unused, double *out_9152136137538215632) {
  H_25(state, unused, out_9152136137538215632);
}
void car_h_24(double *state, double *unused, double *out_694198277336709874) {
  h_24(state, unused, out_694198277336709874);
}
void car_H_24(double *state, double *unused, double *out_5736682337369012848) {
  H_24(state, unused, out_5736682337369012848);
}
void car_h_30(double *state, double *unused, double *out_2984511561861269912) {
  h_30(state, unused, out_2984511561861269912);
}
void car_H_30(double *state, double *unused, double *out_6776274977664087357) {
  H_30(state, unused, out_6776274977664087357);
}
void car_h_26(double *state, double *unused, double *out_6665923047582284564) {
  h_26(state, unused, out_6665923047582284564);
}
void car_H_26(double *state, double *unused, double *out_5990081966410535383) {
  H_26(state, unused, out_5990081966410535383);
}
void car_h_27(double *state, double *unused, double *out_1555543571396949539) {
  h_27(state, unused, out_1555543571396949539);
}
void car_H_27(double *state, double *unused, double *out_8951038289464512268) {
  H_27(state, unused, out_8951038289464512268);
}
void car_h_29(double *state, double *unused, double *out_8326378797747300475) {
  h_29(state, unused, out_8326378797747300475);
}
void car_H_29(double *state, double *unused, double *out_6266043633349695173) {
  H_29(state, unused, out_6266043633349695173);
}
void car_h_28(double *state, double *unused, double *out_3446129696263896106) {
  h_28(state, unused, out_3446129696263896106);
}
void car_H_28(double *state, double *unused, double *out_7098301423290325869) {
  H_28(state, unused, out_7098301423290325869);
}
void car_h_31(double *state, double *unused, double *out_6020542932501928708) {
  h_31(state, unused, out_6020542932501928708);
}
void car_H_31(double *state, double *unused, double *out_6616290068643886859) {
  H_31(state, unused, out_6616290068643886859);
}
void car_predict(double *in_x, double *in_P, double *in_Q, double dt) {
  predict(in_x, in_P, in_Q, dt);
}
void car_set_mass(double x) {
  set_mass(x);
}
void car_set_rotational_inertia(double x) {
  set_rotational_inertia(x);
}
void car_set_center_to_front(double x) {
  set_center_to_front(x);
}
void car_set_center_to_rear(double x) {
  set_center_to_rear(x);
}
void car_set_stiffness_front(double x) {
  set_stiffness_front(x);
}
void car_set_stiffness_rear(double x) {
  set_stiffness_rear(x);
}
}

const EKF car = {
  .name = "car",
  .kinds = { 25, 24, 30, 26, 27, 29, 28, 31 },
  .feature_kinds = {  },
  .f_fun = car_f_fun,
  .F_fun = car_F_fun,
  .err_fun = car_err_fun,
  .inv_err_fun = car_inv_err_fun,
  .H_mod_fun = car_H_mod_fun,
  .predict = car_predict,
  .hs = {
    { 25, car_h_25 },
    { 24, car_h_24 },
    { 30, car_h_30 },
    { 26, car_h_26 },
    { 27, car_h_27 },
    { 29, car_h_29 },
    { 28, car_h_28 },
    { 31, car_h_31 },
  },
  .Hs = {
    { 25, car_H_25 },
    { 24, car_H_24 },
    { 30, car_H_30 },
    { 26, car_H_26 },
    { 27, car_H_27 },
    { 29, car_H_29 },
    { 28, car_H_28 },
    { 31, car_H_31 },
  },
  .updates = {
    { 25, car_update_25 },
    { 24, car_update_24 },
    { 30, car_update_30 },
    { 26, car_update_26 },
    { 27, car_update_27 },
    { 29, car_update_29 },
    { 28, car_update_28 },
    { 31, car_update_31 },
  },
  .Hes = {
  },
  .sets = {
    { "mass", car_set_mass },
    { "rotational_inertia", car_set_rotational_inertia },
    { "center_to_front", car_set_center_to_front },
    { "center_to_rear", car_set_center_to_rear },
    { "stiffness_front", car_set_stiffness_front },
    { "stiffness_rear", car_set_stiffness_rear },
  },
  .extra_routines = {
  },
};

ekf_lib_init(car)
