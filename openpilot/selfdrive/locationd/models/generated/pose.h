#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void pose_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_err_fun(double *nom_x, double *delta_x, double *out_8760976694843722585);
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_43912959781476086);
void pose_H_mod_fun(double *state, double *out_7299666891344506350);
void pose_f_fun(double *state, double dt, double *out_8034507002781912440);
void pose_F_fun(double *state, double dt, double *out_1438095572352487590);
void pose_h_4(double *state, double *unused, double *out_6465945623265405794);
void pose_H_4(double *state, double *unused, double *out_1438529340738482788);
void pose_h_10(double *state, double *unused, double *out_648283545540513810);
void pose_H_10(double *state, double *unused, double *out_3602654715956183362);
void pose_h_13(double *state, double *unused, double *out_4712435644913014);
void pose_H_13(double *state, double *unused, double *out_4650803166070815589);
void pose_h_14(double *state, double *unused, double *out_3818899265695519350);
void pose_H_14(double *state, double *unused, double *out_5401770197077967317);
void pose_predict(double *in_x, double *in_P, double *in_Q, double dt);
}