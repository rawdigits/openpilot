#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void pose_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_err_fun(double *nom_x, double *delta_x, double *out_455516311871516666);
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_4129318549302704896);
void pose_H_mod_fun(double *state, double *out_291361178655748996);
void pose_f_fun(double *state, double dt, double *out_6277713955818918611);
void pose_F_fun(double *state, double dt, double *out_3051886930390844105);
void pose_h_4(double *state, double *unused, double *out_1179958653059836279);
void pose_H_4(double *state, double *unused, double *out_3634206011302561399);
void pose_h_10(double *state, double *unused, double *out_7917951398739470562);
void pose_H_10(double *state, double *unused, double *out_5574544512634486876);
void pose_h_13(double *state, double *unused, double *out_7282516462007542478);
void pose_H_13(double *state, double *unused, double *out_6846479836634894200);
void pose_h_14(double *state, double *unused, double *out_7084974374367104635);
void pose_H_14(double *state, double *unused, double *out_551417579007189103);
void pose_predict(double *in_x, double *in_P, double *in_Q, double dt);
}