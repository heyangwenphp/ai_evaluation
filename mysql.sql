CREATE TABLE `lv_models` (
  `id` int(4) unsigned NOT NULL AUTO_INCREMENT,
  `title` varchar(255) DEFAULT NULL,
  `name` varchar(255) DEFAULT NULL,
  `sort` int(4) DEFAULT NULL COMMENT '排序，值越小越靠前',
  `types` tinyint(1) DEFAULT '0' COMMENT '类型 0国内 1国外',
  `status` tinyint(1) DEFAULT '0' COMMENT '状态 0启用 1停用',
  `is_del` tinyint(1) DEFAULT '0' COMMENT '0显示 1删除',
  `createTime` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `updateTime` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='模型表';


CREATE TABLE `lv_question` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT '对话id',
  `user_id` int(11) unsigned NOT NULL COMMENT '操作用户',
  `question` varchar(1024) DEFAULT NULL COMMENT '问题',
  `file_id` int(11) NOT NULL COMMENT '文件id',
  `models_id` varchar(1024) DEFAULT NULL  COMMENT '选用的模型id',
  `status` tinyint(1) DEFAULT '0' COMMENT '运行状态 0未运行 1运行中 2完成 3失败',
  `is_del` tinyint(1) DEFAULT '0' COMMENT '1删除 0正常',
  `createTime` datetime DEFAULT CURRENT_TIMESTAMP,
  `updateTime` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='对话表';


CREATE TABLE `lv_question_bank` (
  `id` int(4) unsigned NOT NULL AUTO_INCREMENT COMMENT 'id',
  `question_id` int(11) NOT NULL COMMENT '对话问题id',
  `cases` tinyint(1) DEFAULT '0' COMMENT '案例 0主观题 1 客观题',
  `question` text NOT NULL COMMENT '题目',
  `standard_answer` text NOT NULL COMMENT '标准答案',
  `standard` text NOT NULL COMMENT '打分标准',
  `dimension` varchar(256) DEFAULT NULL COMMENT '维度',
  `is_del` tinyint(1) DEFAULT '0' COMMENT '0正常 1 删除',
  `createTime` datetime DEFAULT CURRENT_TIMESTAMP,
  `updateTime` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='题目表';

CREATE TABLE `lv_question_answer` (
  `id` int(4) unsigned NOT NULL AUTO_INCREMENT COMMENT 'id',
  `question_id` int(11) NOT NULL COMMENT '对话问题id',
  `cases` tinyint(1) DEFAULT '0' COMMENT '案例 0主观题 1 客观题',
  `question_bank_id` int(11) NOT NULL COMMENT '问题id',
  `models_id` int(11) NOT NULL COMMENT '模型id',
  `answer_content`text NOT NULL COMMENT '回答内容',
  `score` varchar(256) DEFAULT NULL COMMENT '分数',
  `full_mark` varchar(256) DEFAULT NULL COMMENT '总分',
  `according` text NOT NULL COMMENT '打分标准',
  `is_del` tinyint(1) DEFAULT '0' COMMENT '0正常 1 删除',
  `createTime` datetime DEFAULT CURRENT_TIMESTAMP,
  `updateTime` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='题目回答表';



CREATE TABLE `lv_dialogue_history` (
  `id` int(4) unsigned NOT NULL AUTO_INCREMENT COMMENT 'id',
  `question_id` int(11) NOT NULL COMMENT '对话问题id',
  `cases` tinyint(1) DEFAULT '0' COMMENT '案例 0主观题 1 客观题',
  `content` text NOT NULL COMMENT '内容',
   `file_name` varchar(256) DEFAULT NULL COMMENT '文件名称',
   `path` varchar(256) DEFAULT NULL COMMENT '文件路径',
  `role` tinyint(1) DEFAULT '0' COMMENT '对话角色 0系统 1 用户',
  `is_del` tinyint(1) DEFAULT '0' COMMENT '0正常 1 删除',
  `createTime` datetime DEFAULT CURRENT_TIMESTAMP,
  `updateTime` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC COMMENT='对话历史表';


还要增加一组数据proportion_list，proportion_list的值是[{"dimension":"dimension","domestic_model_total_score":6.00,"foreign_models_total_score":0}],
其中domestic_model_total_score是国内模型的总得分除以国内模型数量，foreign_models_total_score是国外模型的总得分除以国内模型数量。model_info.types为0的是国内模型，为1的是国外模型