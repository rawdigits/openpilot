#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void pose_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_err_fun(double *nom_x, double *delta_x, double *out_3394550637581824468);
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_774672115471856853);
void pose_H_mod_fun(double *state, double *out_7710816715974909147);
void pose_f_fun(double *state, double dt, double *out_5487839870694824154);
void pose_F_fun(double *state, double dt, double *out_5336850415855987983);
void pose_h_4(double *state, double *unused, double *out_7487667227305404692);
void pose_H_4(double *state, double *unused, double *out_3939009506131001575);
void pose_h_10(double *state, double *unused, double *out_1655604040140950053);
void pose_H_10(double *state, double *unused, double *out_4967479801708401183);
void pose_h_13(double *state, double *unused, double *out_8625473817892073850);
void pose_H_13(double *state, double *unused, double *out_726735680798668774);
void pose_h_14(double *state, double *unused, double *out_8584103974170844119);
void pose_H_14(double *state, double *unused, double *out_7021797938426373871);
void pose_predict(double *in_x, double *in_P, double *in_Q, double dt);
}